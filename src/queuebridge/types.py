from __future__ import annotations

from typing import Any, TypedDict

QB_TAG = "__qb__"
QB_VERSION = 1

ALLOWED_MODULE_PREFIXES: tuple[str, ...] = ()


class QBEnvelope(TypedDict):
    t: str
    v: int
    d: Any


class QueuebridgeError(Exception):
    """Base exception for queuebridge."""


class QueuebridgeEncodeError(QueuebridgeError):
    """Raised when a value cannot be encoded."""


class QueuebridgeDecodeError(QueuebridgeError):
    """Raised when a wire value cannot be decoded."""


class QueuebridgeSecurityError(QueuebridgeDecodeError):
    """Raised when FQN import is blocked by security policy."""
