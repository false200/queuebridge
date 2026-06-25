from __future__ import annotations

from typing import Any, Generic, TypeVar, cast

from queuebridge.codec import decode

T = TypeVar("T")


class TypedAsyncResult(Generic[T]):
    """Wraps Celery AsyncResult with typed .get() decoding."""

    def __init__(self, async_result: Any, return_type: type[T]) -> None:
        self._ar = async_result
        self._return_type = return_type

    def get(self, *args: Any, **kwargs: Any) -> T:
        raw = self._ar.get(*args, **kwargs)
        return cast(T, decode(raw, self._return_type))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._ar, name)


def typed_result(async_result: Any, return_type: type[T]) -> TypedAsyncResult[T]:
    return TypedAsyncResult(async_result, return_type)
