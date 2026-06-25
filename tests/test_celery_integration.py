from __future__ import annotations

import pytest
from kombu.exceptions import EncodeError

pytest.importorskip("celery")

from celery import Celery

from queuebridge.celery import register_queuebridge, typed_result
from tests.conftest import OrderCreate, OrderResult


@pytest.fixture
def celery_app() -> Celery:
    app = Celery("test", broker="memory://", backend="cache+memory://")
    app.conf.update(
        task_always_eager=True,
        task_store_eager_result=True,
    )
    register_queuebridge(app)

    @app.task(pydantic=True)
    def process_order(order: OrderCreate) -> OrderResult:
        assert isinstance(order, OrderCreate)
        return OrderResult(id=order.id, status="processed")

    app.process_order = process_order  # type: ignore[attr-defined]
    return app


def test_delay_model_eager(celery_app: Celery) -> None:
    result = celery_app.process_order.delay(OrderCreate(id=1, sku="ABC"))  # type: ignore[attr-defined]
    assert result.successful()


def test_typed_result_get(celery_app: Celery) -> None:
    ar = celery_app.process_order.delay(OrderCreate(id=2, sku="XYZ"))  # type: ignore[attr-defined]
    result = typed_result(ar, OrderResult).get(timeout=10)
    assert isinstance(result, OrderResult)
    assert result.status == "processed"


def test_without_register_raises() -> None:
    app = Celery("bare", broker="memory://", backend="cache+memory://")
    app.conf.update(task_always_eager=True)

    @app.task(pydantic=True)
    def bare_task(order: OrderCreate) -> OrderResult:
        return OrderResult(id=order.id, status="ok")

    with pytest.raises((TypeError, ValueError, EncodeError)):
        bare_task.delay(OrderCreate(id=1, sku="A"))
