from __future__ import annotations

from typing import TYPE_CHECKING

from kombu.serialization import register

from queuebridge.celery.serializer import dumps, loads

if TYPE_CHECKING:
    from celery import Celery


def register_queuebridge(app: Celery, *, strict: bool = False) -> None:
    """Register the ``queuebridge-json`` serializer on a Celery application.

    Configures ``task_serializer``, ``result_serializer``, and ``accept_content``.
    Safe to call multiple times (idempotent).

    Args:
        app: Celery application instance (worker and producer must both call this).
        strict: Reserved for future strict decode behavior on the client.

    Example::

        from celery import Celery
        from queuebridge.celery import register_queuebridge

        app = Celery("myapp", broker="redis://localhost:6379/0")
        register_queuebridge(app)
    """
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