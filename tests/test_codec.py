from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from queuebridge.codec import decode, encode
from queuebridge.types import QB_TAG, QueuebridgeEncodeError
from tests.conftest import OrderCreate, StatusEnum


def test_roundtrip_base_model() -> None:
    original = OrderCreate(id=1, sku="ABC")
    wire = encode(original)
    assert QB_TAG in wire
    restored = decode(wire, OrderCreate)
    assert restored == original
    assert isinstance(restored, OrderCreate)


def test_roundtrip_nested_list() -> None:
    original = [OrderCreate(id=1, sku="A"), OrderCreate(id=2, sku="B")]
    wire = encode(original)
    restored = decode(wire, list[OrderCreate])
    assert restored == original


def test_roundtrip_uuid_datetime_decimal() -> None:
    uid = uuid4()
    dt = datetime(2024, 6, 1, 12, 30, 0)
    d = date(2024, 6, 1)
    t = time(12, 30, 0)
    dec = Decimal("19.99")

    assert decode(encode(uid), UUID) == uid
    assert decode(encode(dt), datetime) == dt
    assert decode(encode(d), date) == d
    assert decode(encode(t), time) == t
    assert decode(encode(dec), Decimal) == dec


def test_roundtrip_enum() -> None:
    wire = encode(StatusEnum.OK)
    assert decode(wire, StatusEnum) == StatusEnum.OK


def test_plain_dict_with_hint() -> None:
    data = {"id": 1, "sku": "ABC"}
    result = decode(data, OrderCreate)
    assert isinstance(result, OrderCreate)
    assert result.id == 1


def test_encode_unsupported_type() -> None:
    from tests.conftest import UnsupportedClass

    with pytest.raises(QueuebridgeEncodeError):
        encode(UnsupportedClass())


def test_roundtrip_tuple() -> None:
    original = (1, OrderCreate(id=1, sku="X"))
    wire = encode(original)
    restored = decode(wire, tuple[int, OrderCreate])
    assert restored == original


def test_roundtrip_set() -> None:
    original = {UUID(int=1), UUID(int=2)}
    wire = encode(original)
    restored = decode(wire, set[UUID])
    assert restored == original
