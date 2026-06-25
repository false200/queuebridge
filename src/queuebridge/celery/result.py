from __future__ import annotations

from typing import Any, Generic, TypeVar, cast

from queuebridge.codec import decode

T = TypeVar("T")


class TypedAsyncResult(Generic[T]):
    """Wraps Celery :class:`~celery.result.AsyncResult` with typed ``get()``.

    Proxies all other attributes (``.id``, ``.state``, ``.ready()``, etc.) to
    the underlying async result.

    Args:
        async_result: Celery async result from ``task.delay()`` or ``apply_async()``.
        return_type: Pydantic model or type hint for the task return value.

    Example::

        ar = process_order.delay(OrderCreate(id=1, sku="X"))
        result = TypedAsyncResult(ar, OrderResult).get(timeout=10)
    """

    def __init__(self, async_result: Any, return_type: type[T]) -> None:
        self._ar = async_result
        self._return_type = return_type

    def get(self, *args: Any, **kwargs: Any) -> T:
        """Block until ready and decode the result to ``return_type``."""
        raw = self._ar.get(*args, **kwargs)
        return cast(T, decode(raw, self._return_type))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._ar, name)


def typed_result(async_result: Any, return_type: type[T]) -> TypedAsyncResult[T]:
    """Create a :class:`TypedAsyncResult` for client-side typed ``get()``.

    Args:
        async_result: Celery async result.
        return_type: Expected return type (usually a Pydantic model).

    Returns:
        Wrapper whose ``get()`` returns ``return_type`` instead of ``dict``.
    """
    return TypedAsyncResult(async_result, return_type)
