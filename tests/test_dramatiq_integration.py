from __future__ import annotations

import pytest

pytest.importorskip("dramatiq")

import dramatiq
from dramatiq import Worker
from dramatiq.brokers.stub import StubBroker
from pydantic import validate_call

from queuebridge.dramatiq import register_queuebridge
from tests.conftest import OrderCreate

received: list[OrderCreate] = []


@pytest.fixture
def broker() -> StubBroker:
    broker = StubBroker()
    dramatiq.set_broker(broker)
    register_queuebridge(broker)

    @dramatiq.actor
    @validate_call
    def process(order: OrderCreate) -> None:
        received.append(order)

    broker.process = process  # type: ignore[attr-defined]
    broker.declare_queue("default")
    return broker


def test_send_model(broker: StubBroker) -> None:
    received.clear()
    worker = Worker(broker, worker_timeout=100)
    worker.start()
    try:
        broker.process.send(OrderCreate(id=1, sku="X"))  # type: ignore[attr-defined]
        broker.join("default", timeout=5000)
    finally:
        worker.stop()
    assert len(received) == 1
    assert isinstance(received[0], OrderCreate)
    assert received[0].sku == "X"
