#!/usr/bin/env python3
"""
Smoke test for queuebridge — complex models + Celery + Dramatiq (no Redis required).

Run after installing from TestPyPI or locally:
    py -3 examples/smoke_test_complex.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validate_call

from queuebridge import decode, encode
from queuebridge.codec import decode_wire


# ---------------------------------------------------------------------------
# Complex domain models (the kind people actually pass to task queues)
# ---------------------------------------------------------------------------


class Priority(str, Enum):
    LOW = "low"
    HIGH = "high"
    CRITICAL = "critical"


class LineItem(BaseModel):
    sku: str
    qty: int = Field(ge=1)
    unit_price: Decimal


class ShippingAddress(BaseModel):
    street: str
    city: str
    country: str = "US"
    geo_id: UUID


class ShipmentRequest(BaseModel):
    """Nested model with UUID, datetime, Decimal, Enum, and list of models."""

    request_id: UUID
    customer_ref: str
    priority: Priority
    created_at: datetime
    items: list[LineItem]
    ship_to: ShippingAddress
    notes: Optional[str] = None
    tags: set[str] = Field(default_factory=set)


class ShipmentResult(BaseModel):
    request_id: UUID
    tracking_code: str
    total: Decimal
    shipped_at: datetime
    item_count: int


def make_sample_request() -> ShipmentRequest:
    return ShipmentRequest(
        request_id=uuid4(),
        customer_ref="CUST-8842",
        priority=Priority.HIGH,
        created_at=datetime.now(timezone.utc),
        items=[
            LineItem(sku="WIDGET-01", qty=3, unit_price=Decimal("19.99")),
            LineItem(sku="GADGET-42", qty=1, unit_price=Decimal("149.50")),
        ],
        ship_to=ShippingAddress(
            street="42 Queue Lane",
            city="Brooklyn",
            geo_id=uuid4(),
        ),
        notes="Fragile — handle with care",
        tags={"express", "insured"},
    )


# ---------------------------------------------------------------------------
# 1. Core codec roundtrip
# ---------------------------------------------------------------------------


def test_codec_roundtrip() -> None:
    original = make_sample_request()
    wire = encode(original)
    assert isinstance(wire, dict)
    restored = decode(wire, ShipmentRequest)
    assert restored == original
    assert isinstance(restored.ship_to.geo_id, UUID)
    assert isinstance(restored.items[0].unit_price, Decimal)
    assert restored.priority is Priority.HIGH
    print("  [OK] encode/decode roundtrip (nested models, UUID, Decimal, Enum, set)")


def test_codec_list_of_models() -> None:
    batch = [make_sample_request(), make_sample_request()]
    wire = encode(batch)
    restored = decode(wire, list[ShipmentRequest])
    assert len(restored) == 2
    assert all(isinstance(r, ShipmentRequest) for r in restored)
    print("  [OK] list[ShipmentRequest] roundtrip")


# ---------------------------------------------------------------------------
# 2. Celery (eager mode — no broker needed)
# ---------------------------------------------------------------------------


def test_celery_eager() -> None:
    from celery import Celery

    from queuebridge.celery import register_queuebridge, typed_result

    app = Celery("smoke", broker="memory://", backend="cache+memory://")
    app.conf.update(task_always_eager=True, task_store_eager_result=True)
    register_queuebridge(app)

    @app.task(pydantic=True)
    def fulfill_shipment(req: ShipmentRequest) -> ShipmentResult:
        assert isinstance(req, ShipmentRequest)
        assert isinstance(req.items[0].unit_price, Decimal)
        total = sum(i.unit_price * i.qty for i in req.items)
        return ShipmentResult(
            request_id=req.request_id,
            tracking_code=f"TRK-{req.customer_ref}",
            total=total,
            shipped_at=datetime.now(timezone.utc),
            item_count=len(req.items),
        )

    request = make_sample_request()
    async_result = fulfill_shipment.delay(request)
    assert async_result.successful(), async_result.traceback

    raw = async_result.get()
    assert isinstance(raw, dict), "Celery .get() still returns dict without typed_result"

    result = typed_result(async_result, ShipmentResult).get()
    assert isinstance(result, ShipmentResult)
    assert result.tracking_code == f"TRK-{request.customer_ref}"
    assert result.total == Decimal("19.99") * 3 + Decimal("149.50")
    print("  [OK] Celery delay(model) + typed_result().get() -> ShipmentResult")


# ---------------------------------------------------------------------------
# 3. Dramatiq (StubBroker + in-process worker)
# ---------------------------------------------------------------------------


def test_dramatiq_stub() -> None:
    import dramatiq
    from dramatiq import Worker
    from dramatiq.brokers.stub import StubBroker

    from queuebridge.dramatiq import register_queuebridge

    received: list[ShipmentRequest] = []

    broker = StubBroker()
    dramatiq.set_broker(broker)
    register_queuebridge(broker)

    @dramatiq.actor
    @validate_call
    def receive_shipment(req: ShipmentRequest) -> None:
        received.append(req)

    broker.declare_queue("default")
    worker = Worker(broker, worker_timeout=100)
    worker.start()
    try:
        receive_shipment.send(make_sample_request())
        broker.join("default", timeout=5000)
    finally:
        worker.stop()

    assert len(received) == 1
    assert isinstance(received[0], ShipmentRequest)
    assert received[0].priority in Priority
    print("  [OK] Dramatiq send(model) -> validate_call receives ShipmentRequest")


# ---------------------------------------------------------------------------
# 4. Wire format sanity (what actually hits the broker)
# ---------------------------------------------------------------------------


def test_wire_has_tags() -> None:
    req = make_sample_request()
    wire = encode(req)
    assert "__qb__" in wire
    assert wire["__qb__"]["t"].endswith("ShipmentRequest")
    unwrapped = decode_wire(wire)
    assert isinstance(unwrapped, ShipmentRequest)
    print("  [OK] wire format uses __qb__ tags; decode_wire unwraps to model")


def main() -> int:
    print("queuebridge smoke test - complex models\n")
    tests = [
        ("Core codec", test_codec_roundtrip),
        ("List of models", test_codec_list_of_models),
        ("Wire format", test_wire_has_tags),
        ("Celery eager", test_celery_eager),
        ("Dramatiq stub", test_dramatiq_stub),
    ]
    failed = 0
    for name, fn in tests:
        print(f"\n{name}:")
        try:
            fn()
        except Exception as exc:
            print(f"  [FAIL] {exc}")
            failed += 1

    print()
    if failed:
        print(f"FAILED — {failed} check(s)")
        return 1
    print("ALL CHECKS PASSED — queuebridge is working")
    return 0


if __name__ == "__main__":
    sys.exit(main())
