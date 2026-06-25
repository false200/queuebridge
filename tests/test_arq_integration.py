from __future__ import annotations

import pytest

pytest.importorskip("arq")
pytest.importorskip("msgpack")

from pydantic import validate_call

from queuebridge.arq import get_serializer_pair, qb_task, typed_result
from queuebridge.codec import encode
from tests.models import OrderCreate, OrderResult

serialize, deserialize = get_serializer_pair()


def test_serialize_job_dict_with_model() -> None:
    job = {
        "t": 1,
        "f": "process_order",
        "a": [],
        "k": {"order": encode(OrderCreate(id=1, sku="A"))},
        "et": 0,
    }
    data = serialize(job)
    assert isinstance(data, bytes)
    restored = deserialize(data)
    assert "k" in restored
    assert "__qb__" in restored["k"]["order"]


@qb_task
@validate_call
async def process_order(ctx: dict, order: OrderCreate) -> OrderResult:
    return OrderResult(id=order.id, status="ok")


@pytest.mark.asyncio
async def test_qb_task_decodes_args() -> None:
    wire_order = encode(OrderCreate(id=3, sku="Z"))
    result = await process_order({}, wire_order)
    assert isinstance(result, OrderResult)
    assert result.id == 3


@pytest.mark.asyncio
async def test_typed_result_decode() -> None:
    wire = encode(OrderResult(id=1, status="done"))

    class FakeJob:
        async def result(self) -> object:
            return wire

    result = await typed_result(FakeJob(), OrderResult)
    assert isinstance(result, OrderResult)
    assert result.status == "done"
