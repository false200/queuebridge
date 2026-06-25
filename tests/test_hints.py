from __future__ import annotations

from tests.conftest import OrderCreate, OrderResult
from queuebridge.codec import encode
from queuebridge.hints import decode_args, decode_return, get_task_signature


def process_order(order: OrderCreate) -> OrderResult:
    return OrderResult(id=order.id, status="ok")


def test_get_task_signature() -> None:
    sig = get_task_signature(process_order)
    assert sig.params["order"] is OrderCreate
    assert sig.return_type is OrderResult


def test_decode_args() -> None:
    wire = encode(OrderCreate(id=5, sku="Z"))
    args, kwargs = decode_args(process_order, (), {"order": wire})
    assert isinstance(kwargs["order"], OrderCreate)
    assert kwargs["order"].id == 5


def test_decode_return() -> None:
    wire = encode(OrderResult(id=1, status="done"))
    result = decode_return(process_order, wire)
    assert isinstance(result, OrderResult)
    assert result.status == "done"
