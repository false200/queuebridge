from __future__ import annotations

from typing import TYPE_CHECKING

from kombu.serialization import register

from queuebridge.celery.serializer import dumps, loads

if TYPE_CHECKING:
    from celery import Celery


def register_queuebridge(app: Celery, *, strict: bool = False) -> None:
    """Register queuebridge-json serializer on a Celery app. Idempotent."""
    if getattr(app, "_queuebridge_installed", False):
        return

    register(
        "queuebridge-json",
        dumps,
        loads,
        content_type="application/json",
        content_encoding="utf-8",
    )
    app.conf.update(
        task_serializer="queuebridge-json",
        result_serializer="queuebridge-json",
        accept_content=["json", "queuebridge-json"],
        result_accept_content=["json", "queuebridge-json"],
    )
    app._queuebridge_installed = True
    app._queuebridge_strict = strict
