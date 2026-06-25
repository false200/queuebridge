from __future__ import annotations

import json
from typing import Any

from queuebridge.codec import encode


def dumps(obj: Any) -> str:
    # Plain model dicts so Celery pydantic=True can validate kwargs.
    return json.dumps(encode(obj, tag_models=False))


def loads(data: str) -> Any:
    return json.loads(data)
