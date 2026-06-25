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
    """Return ``(serialize, deserialize)`` for Arq ``WorkerSettings`` and ``create_pool``.

    Both the worker and the client **must** use the same pair.

    Returns:
        Tuple of callables compatible with Arq's ``job_serializer`` / ``job_deserializer``.

    Example::

        serialize, deserialize = get_serializer_pair()

        class WorkerSettings:
            job_serializer = serialize
            job_deserializer = deserialize
    """
    return serialize, deserialize


def qb_task(fn: F) -> F:
    """Decode wire args/kwargs before the wrapped async Arq task runs.

    Apply **outside** ``@validate_call``::

        @qb_task
        @validate_call
        async def process(ctx, order: OrderCreate): ...

    Args:
        fn: Async task function registered with Arq.

    Returns:
        Wrapped coroutine with decoded arguments.
    """

    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        decoded_args, decoded_kwargs = decode_args(fn, args, kwargs)
        return await fn(*decoded_args, **decoded_kwargs)

    return wrapper  # type: ignore[return-value]


async def typed_result(job: Any, return_type: type[T]) -> T:
    """Await ``job.result()`` and decode into a Pydantic model.

    Args:
        job: Arq :class:`~arq.jobs.Job` instance.
        return_type: Expected result type.

    Returns:
        Decoded result (e.g. ``OrderResult``).

    Example::

        job = await pool.enqueue_job("process_order", order=data)
        result = await typed_result(job, OrderResult)
    """
    raw = await job.result()
    return cast(T, decode(raw, return_type))
