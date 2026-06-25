"""Type hints utilities for decoding task arguments and return values."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, get_type_hints

from queuebridge.codec import decode

_SKIP_PARAMS = frozenset({"self", "cls", "ctx"})

_signature_cache: dict[int, TaskSignature] = {}


@dataclass(frozen=True)
class TaskSignature:
    """Cached type hints for a task function.

    Attributes:
        params: Mapping of parameter name to annotation (skips ``self``, ``cls``, ``ctx``).
        return_type: Return annotation, or ``Any`` if missing.
    """

    params: dict[str, Any]
    return_type: Any


def get_task_signature(fn: Callable[..., Any]) -> TaskSignature:
    """Extract and cache parameter/return type hints from a callable.

    Args:
        fn: Task function (sync, async, or decorated).

    Returns:
        :class:`TaskSignature` with ``params`` and ``return_type``.
    """
    cache_key = id(fn)
    if cache_key in _signature_cache:
        return _signature_cache[cache_key]

    hints = get_type_hints(fn, include_extras=True)
    sig = inspect.signature(fn)
    params: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if name in _SKIP_PARAMS:
            continue
        if name in hints:
            params[name] = hints[name]

    return_type = hints.get("return", Any)
    task_sig = TaskSignature(params=params, return_type=return_type)
    _signature_cache[cache_key] = task_sig
    return task_sig


def decode_args(
    fn: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Decode wire ``args`` and ``kwargs`` using ``fn``'s type hints.

    Skips decoding for ``self``, ``cls``, and ``ctx`` parameters (Arq/Celery).

    Args:
        fn: Task function whose annotations guide decoding.
        args: Positional wire values.
        kwargs: Keyword wire values.

    Returns:
        Tuple of ``(decoded_args, decoded_kwargs)``.
    """
    sig = get_task_signature(fn)
    inspect_sig = inspect.signature(fn)
    all_param_names = list(inspect_sig.parameters.keys())

    new_args_list: list[Any] = []
    for i, arg in enumerate(args):
        if i < len(all_param_names):
            name = all_param_names[i]
            if name in _SKIP_PARAMS:
                new_args_list.append(arg)
            else:
                hint = sig.params.get(name, Any)
                new_args_list.append(decode(arg, hint))
        else:
            new_args_list.append(arg)

    new_kwargs = {k: decode(v, sig.params.get(k, Any)) for k, v in kwargs.items()}
    return tuple(new_args_list), new_kwargs


def decode_return(fn: Callable[..., Any], result: Any) -> Any:
    """Decode a task return value using ``fn``'s return type hint.

    Args:
        fn: Task function.
        result: Wire return value from the result backend.

    Returns:
        Decoded Python object.
    """
    sig = get_task_signature(fn)
    return decode(result, sig.return_type)
