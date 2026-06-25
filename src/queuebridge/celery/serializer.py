from __future__ import annotations

import json
from typing import Any
from queuebridge.codec import encode


def dumps(obj: Any) -> str:
    """Kombu encoder: JSON-serialize a Celery message body.

    Uses ``encode(..., tag_models=False)`` so Celery ``pydantic=True`` can
    validate plain dicts on the worker.

    Args:
        obj: Celery/kombu message dict (``task``, ``args``, ``kwargs``, ...).

    Returns:
        JSON string.
    """
    return json.dumps(encode(obj, tag_models=False))


def loads(data: str) -> Any:
    """Kombu decoder: parse JSON message body.

    Returns wire dicts; worker-side ``pydantic=True`` validates models.

    Args:
        data: JSON string from the broker.

    Returns:
        Parsed message dict.
    """
    return json.loads(data)
