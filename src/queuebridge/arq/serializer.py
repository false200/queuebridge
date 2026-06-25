from __future__ import annotations

from typing import Any

import msgpack

from queuebridge.codec import encode


def serialize(d: dict[str, Any]) -> bytes:
    packed: bytes = msgpack.packb(encode(d), use_bin_type=True)
    return packed


def deserialize(b: bytes) -> dict[str, Any]:
    result = msgpack.unpackb(b, raw=False)
    if not isinstance(result, dict):
        raise TypeError(f"expected dict from deserializer, got {type(result)}")
    return result
