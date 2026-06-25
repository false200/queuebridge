from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

from queuebridge.arq.serializer import deserialize, serialize
from queuebridge.codec import decode
from queuebridge.hints import decode_args

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def get_serializer_pair() -> tuple[Callable[[dict[str, Any]], bytes], Callable[[bytes], dict[str, Any]]]:
    """Return msgpack serialize/deserialize callables for Arq worker and client."""
    return serialize, deserialize


def qb_task(fn: F) -> F:
    """Decode wire args/kwargs before the wrapped async task runs."""

    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        decoded_args, decoded_kwargs = decode_args(fn, args, kwargs)
        return await fn(*decoded_args, **decoded_kwargs)

    return wrapper  # type: ignore[return-value]


async def typed_result(job: Any, return_type: type[T]) -> T:
    """Await ``job.result()`` and decode the payload into ``return_type``."""
    raw = await job.result()
    return cast(T, decode(raw, return_type))
