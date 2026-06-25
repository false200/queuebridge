from __future__ import annotations

from typing import Any

import msgpack

from queuebridge.codec import encode


def serialize(d: dict[str, Any]) -> bytes:
    """Arq job serializer: msgpack over queuebridge-encoded dict.

    Args:
        d: Arq job dict (``t``, ``f``, ``a``, ``k``, ``et``, ...).

    Returns:
        msgpack bytes safe for Redis storage.
    """
    packed: bytes = msgpack.packb(encode(d), use_bin_type=True)
    return packed


def deserialize(b: bytes) -> dict[str, Any]:
    """Arq job deserializer: unpack msgpack to wire dict.

    Args:
        b: Bytes from the Arq queue.

    Returns:
        Job dict still in wire format; use ``@qb_task`` to decode at task boundary.
    """
    result = msgpack.unpackb(b, raw=False)
    if not isinstance(result, dict):
        raise TypeError(f"expected dict from deserializer, got {type(result)}")
    return result
