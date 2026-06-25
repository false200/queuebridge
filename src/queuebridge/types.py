"""Wire format constants, envelope types, and exceptions."""

from __future__ import annotations

from typing import Any, TypedDict

QB_TAG = "__qb__"
"""JSON key for tagged queuebridge envelopes on the wire."""

QB_VERSION = 1
"""Current wire format version (stored in each envelope)."""

ALLOWED_MODULE_PREFIXES: tuple[str, ...] = ()
"""Module prefixes allowed for FQN import during decode.

Empty tuple means all modules are allowed. Set to e.g. ``("myapp.",)`` in v0.2+.
"""


class QBEnvelope(TypedDict):
    """Shape of the inner envelope at ``value[QB_TAG]``."""

    t: str
    v: int
    d: Any


class QueuebridgeError(Exception):
    """Base exception for queuebridge."""


class QueuebridgeEncodeError(QueuebridgeError):
    """Raised when a value cannot be encoded (unsupported type)."""


class QueuebridgeDecodeError(QueuebridgeError):
    """Raised when a wire value cannot be decoded."""


class QueuebridgeSecurityError(QueuebridgeDecodeError):
    """Raised when FQN import is blocked by ``ALLOWED_MODULE_PREFIXES``."""
