"""queuebridge: bidirectional Pydantic serialization for task queues.

Pass Pydantic models to ``.delay()``, ``.send()``, or ``enqueue_job()``.
Get models back from results. Supports Celery, Dramatiq, and Arq.

Example::

    from queuebridge import encode, decode
    from queuebridge.celery import register_queuebridge, typed_result
"""

from queuebridge.__version__ import __version__
from queuebridge.codec import decode, encode

__all__ = ["decode", "encode", "__version__"]
