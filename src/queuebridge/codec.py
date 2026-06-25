"""Core encode/decode codec and wire-format helpers for queuebridge."""

from __future__ import annotations

import importlib
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any, Union, get_args, get_origin
from uuid import UUID

from pydantic import BaseModel, RootModel, TypeAdapter
from typing_extensions import get_origin as te_get_origin

from queuebridge.types import (
    ALLOWED_MODULE_PREFIXES,
    QB_TAG,
    QB_VERSION,
    QueuebridgeDecodeError,
    QueuebridgeEncodeError,
    QueuebridgeSecurityError,
)

_BUILTIN_DECODE: dict[str, type[Any]] = {
    "uuid.UUID": UUID,
    "datetime.datetime": datetime,
    "datetime.date": date,
    "datetime.time": time,
    "decimal.Decimal": Decimal,
}


def class_fqn(obj: type[Any] | object) -> str:
    """Return the fully-qualified name of a type or instance.

    Example: ``class_fqn(OrderCreate)`` -> ``"myapp.models.OrderCreate"``.

    Args:
        obj: A class or instance.

    Returns:
        ``"{module}.{qualname}"`` string used in ``__qb__`` envelopes.
    """
    cls = obj if isinstance(obj, type) else type(obj)
    return f"{cls.__module__}.{cls.__qualname__}"


def import_fqn(fqn: str) -> type[Any]:
    """Import and return a type from its fully-qualified name.

    Used when decoding ``__qb__`` envelopes. Respects ``ALLOWED_MODULE_PREFIXES``
    when that tuple is non-empty.

    Args:
        fqn: e.g. ``"myapp.models.OrderCreate"``.

    Returns:
        The resolved type.

    Raises:
        QueuebridgeSecurityError: If the module prefix is blocked.
        QueuebridgeDecodeError: If the FQN is invalid or not a type.
    """
    module_name, _, qualname = fqn.rpartition(".")
    if not module_name:
        raise QueuebridgeDecodeError(f"invalid FQN: {fqn}")
    if ALLOWED_MODULE_PREFIXES and not module_name.startswith(ALLOWED_MODULE_PREFIXES):
        raise QueuebridgeSecurityError(f"import blocked: {fqn}")
    module = importlib.import_module(module_name)
    obj: Any = module
    for part in qualname.split("."):
        obj = getattr(obj, part)
    if not isinstance(obj, type):
        raise QueuebridgeDecodeError(f"FQN does not resolve to a type: {fqn}")
    return obj


def _make_envelope(type_name: str, payload: Any) -> dict[str, Any]:
    return {QB_TAG: {"t": type_name, "v": QB_VERSION, "d": payload}}


def is_qb_envelope(value: Any) -> bool:
    """Return True if ``value`` is a queuebridge ``__qb__`` tagged envelope."""
    if not isinstance(value, dict) or QB_TAG not in value:
        return False
    inner = value[QB_TAG]
    return (
        isinstance(inner, dict)
        and "t" in inner
        and "v" in inner
        and "d" in inner
    )


def _origin(hint: Any) -> Any:
    origin = get_origin(hint)
    if origin is None:
        origin = te_get_origin(hint)
    return origin


def _is_base_model_type(tp: Any) -> bool:
    return isinstance(tp, type) and issubclass(tp, BaseModel)


def _decode_envelope(value: dict[str, Any]) -> Any:
    inner = value[QB_TAG]
    type_name: str = inner["t"]
    payload: Any = inner["d"]

    if type_name in _BUILTIN_DECODE:
        builtin = _BUILTIN_DECODE[type_name]
        if builtin is UUID:
            return UUID(payload)
        if builtin is datetime:
            return datetime.fromisoformat(payload)
        if builtin is date:
            return date.fromisoformat(payload)
        if builtin is time:
            return time.fromisoformat(payload)
        if builtin is Decimal:
            return Decimal(payload)

    tag_type = import_fqn(type_name)

    if _is_base_model_type(tag_type):
        return tag_type.model_validate(payload)

    if isinstance(tag_type, type) and issubclass(tag_type, Enum):
        return tag_type(payload)

    return TypeAdapter(tag_type).validate_python(payload)


def encode(value: Any, *, tag_models: bool = True) -> Any:
    """Recursively transform a value into a JSON-serializable structure.

    Args:
        value: Python object to encode (models, UUID, datetime, containers, etc.).
        tag_models: When True, wrap ``BaseModel`` instances in ``__qb__`` envelopes.

    Returns:
        JSON-compatible primitives, lists, dicts, or tagged envelopes.

    Raises:
        QueuebridgeEncodeError: If the type is not supported.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value

    if is_qb_envelope(value):
        return value

    if isinstance(value, BaseModel):
        dumped = value.model_dump(mode="json")
        if not tag_models:
            return dumped
        return _make_envelope(class_fqn(value), dumped)

    if isinstance(value, RootModel):
        inner = value.root
        if isinstance(inner, BaseModel):
            dumped = inner.model_dump(mode="json")
            if not tag_models:
                return dumped
            return _make_envelope(class_fqn(inner), dumped)
        return encode(inner, tag_models=tag_models)

    if isinstance(value, UUID):
        return _make_envelope("uuid.UUID", str(value))

    if isinstance(value, datetime):
        return _make_envelope("datetime.datetime", value.isoformat())

    if isinstance(value, date):
        return _make_envelope("datetime.date", value.isoformat())

    if isinstance(value, time):
        return _make_envelope("datetime.time", value.isoformat())

    if isinstance(value, Decimal):
        return _make_envelope("decimal.Decimal", str(value))

    if isinstance(value, Enum):
        return _make_envelope(class_fqn(value.__class__), value.value)

    if isinstance(value, dict):
        return {str(encode(k, tag_models=tag_models)): encode(v, tag_models=tag_models) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [encode(item, tag_models=tag_models) for item in value]

    raise QueuebridgeEncodeError(f"unsupported type: {type(value)}")


def _decode_union(value: Any, hint: Any, *, strict: bool) -> Any:
    args = get_args(hint)
    if not args:
        return value

    adapter = TypeAdapter(hint)
    try:
        return adapter.validate_python(value)
    except Exception:
        pass

    last_error: Exception | None = None
    for arm in args:
        if arm is type(None) and value is None:
            return None
        try:
            return decode(value, arm, strict=False)
        except (QueuebridgeDecodeError, Exception) as exc:
            last_error = exc
            continue

    if strict:
        msg = f"cannot decode union value: {value!r}"
        if last_error:
            msg = f"{msg} (last error: {last_error})"
        raise QueuebridgeDecodeError(msg)
    return value


def decode_wire(value: Any) -> Any:
    """Recursively unwrap ``__qb__`` envelopes without type hints.

    Useful when you know the wire data contains tags but you do not have
    function annotations (e.g. Dramatiq message decode path).

    Args:
        value: Wire data (nested dicts/lists with optional envelopes).

    Returns:
        Python objects with all envelopes resolved.
    """
    if is_qb_envelope(value):
        return _decode_envelope(value)
    if isinstance(value, dict):
        return {k: decode_wire(v) for k, v in value.items()}
    if isinstance(value, list):
        return [decode_wire(v) for v in value]
    return value


def decode(value: Any, hint: Any = Any, *, strict: bool = False) -> Any:
    """Recursively decode a wire value to Python using an optional type hint.

    Args:
        value: Wire data (primitives, containers, or ``__qb__`` envelopes).
        hint: Type annotation used for validation (e.g. ``OrderCreate``).
        strict: Raise ``QueuebridgeDecodeError`` when decoding fails.

    Returns:
        Decoded Python object.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value

    if is_qb_envelope(value):
        return _decode_envelope(value)

    origin = _origin(hint)

    if origin is list:
        inner_args = get_args(hint)
        inner = inner_args[0] if inner_args else Any
        if isinstance(value, list):
            return [decode(item, inner, strict=strict) for item in value]
        if strict:
            raise QueuebridgeDecodeError(f"expected list, got {type(value)}")
        return value

    if origin is tuple:
        inner_args = get_args(hint)
        if isinstance(value, list):
            if inner_args and len(inner_args) == 2 and inner_args[1] is ...:
                return tuple(decode(item, inner_args[0], strict=strict) for item in value)
            if inner_args:
                return tuple(
                    decode(item, inner_args[i] if i < len(inner_args) else Any, strict=strict)
                    for i, item in enumerate(value)
                )
            return tuple(value)
        if strict:
            raise QueuebridgeDecodeError(f"expected list for tuple hint, got {type(value)}")
        return value

    if origin is set:
        inner_args = get_args(hint)
        inner = inner_args[0] if inner_args else Any
        if isinstance(value, list):
            return {decode(item, inner, strict=strict) for item in value}
        if strict:
            raise QueuebridgeDecodeError(f"expected list for set hint, got {type(value)}")
        return value

    if origin is dict:
        args = get_args(hint)
        key_hint = args[0] if args else Any
        val_hint = args[1] if len(args) > 1 else Any
        if isinstance(value, dict):
            return {
                decode(k, key_hint, strict=strict): decode(v, val_hint, strict=strict)
                for k, v in value.items()
            }
        if strict:
            raise QueuebridgeDecodeError(f"expected dict, got {type(value)}")
        return value

    if origin is Union:
        return _decode_union(value, hint, strict=strict)

    if _is_base_model_type(hint) and isinstance(value, dict):
        return hint.model_validate(value)

    if hint is not Any:
        try:
            return TypeAdapter(hint).validate_python(value)
        except Exception as exc:
            if strict:
                raise QueuebridgeDecodeError(f"cannot decode value with hint {hint!r}: {exc}") from exc
            return value

    if strict:
        raise QueuebridgeDecodeError(f"cannot decode value without hint: {value!r}")
    return value
