#!/usr/bin/env python3
"""PyPI install verification - complex queuebridge smoke test (isolated from repo source)."""

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
        notes="Fragile - handle with care",
        tags={"express", "insured"},
    )


def test_codec_roundtrip() -> None:
    original = make_sample_request()
    wire = encode(original)
    restored = decode(wire, ShipmentRequest)
    assert restored == original
    print("  [OK] encode/decode roundtrip")


def test_codec_list() -> None:
    batch = [make_sample_request(), make_sample_request()]
    restored = decode(encode(batch), list[ShipmentRequest])
    assert len(restored) == 2
    print("  [OK] list[ShipmentRequest] roundtrip")


def test_wire_tags() -> None:
    wire = encode(make_sample_request())
    assert "__qb__" in wire
    assert isinstance(decode_wire(wire), ShipmentRequest)
    print("  [OK] __qb__ wire format")


def test_celery() -> None:
    from celery import Celery
    from queuebridge.celery import register_queuebridge, typed_result

    app = Celery("smoke", broker="memory://", backend="cache+memory://")
    app.conf.update(task_always_eager=True, task_store_eager_result=True)
    register_queuebridge(app)

    @app.task(pydantic=True)
    def fulfill(req: ShipmentRequest) -> ShipmentResult:
        total = sum(i.unit_price * i.qty for i in req.items)
        return ShipmentResult(
            request_id=req.request_id,
            tracking_code=f"TRK-{req.customer_ref}",
            total=total,
            shipped_at=datetime.now(timezone.utc),
            item_count=len(req.items),
        )

    req = make_sample_request()
    ar = fulfill.delay(req)
    assert ar.successful()
    result = typed_result(ar, ShipmentResult).get()
    assert result.tracking_code == f"TRK-{req.customer_ref}"
    print("  [OK] Celery delay(model) + typed_result().get()")


def test_dramatiq() -> None:
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
    def receive(req: ShipmentRequest) -> None:
        received.append(req)

    broker.declare_queue("default")
    worker = Worker(broker, worker_timeout=100)
    worker.start()
    try:
        receive.send(make_sample_request())
        broker.join("default", timeout=5000)
    finally:
        worker.stop()

    assert len(received) == 1 and isinstance(received[0], ShipmentRequest)
    print("  [OK] Dramatiq send(model) + validate_call")


def test_arq() -> None:
    from queuebridge.arq import get_serializer_pair, qb_task

    serialize, deserialize = get_serializer_pair()
    job = {
        "t": 1,
        "f": "receive",
        "a": [],
        "k": {"order": encode(make_sample_request())},
        "et": 0,
    }
    roundtrip = deserialize(serialize(job))
    assert "__qb__" in roundtrip["k"]["order"]

    @qb_task
    async def receive(ctx: dict, order: ShipmentRequest) -> ShipmentResult:
        return ShipmentResult(
            request_id=order.request_id,
            tracking_code="ARQ-OK",
            total=Decimal("0"),
            shipped_at=datetime.now(timezone.utc),
            item_count=len(order.items),
        )

    import asyncio

    async def run() -> None:
        wire = encode(make_sample_request())
        result = await receive({}, wire)
        assert isinstance(result, ShipmentResult)

    asyncio.run(run())
    print("  [OK] Arq serializer + qb_task")


def main() -> int:
    import queuebridge

    print(f"Installed queuebridge {queuebridge.__version__} from PyPI\n")
    tests = [
        ("Core codec", test_codec_roundtrip),
        ("List models", test_codec_list),
        ("Wire format", test_wire_tags),
        ("Celery", test_celery),
        ("Dramatiq", test_dramatiq),
        ("Arq", test_arq),
    ]
    failed = 0
    for name, fn in tests:
        print(f"{name}:")
        try:
            fn()
        except Exception as exc:
            print(f"  [FAIL] {exc}")
            failed += 1
    print()
    if failed:
        print(f"FAILED ({failed})")
        return 1
    print("ALL CHECKS PASSED - PyPI install works")
    return 0


if __name__ == "__main__":
    sys.exit(main())
