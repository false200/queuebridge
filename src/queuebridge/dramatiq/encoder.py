from __future__ import annotations

import dramatiq
from dramatiq import JSONEncoder
from dramatiq.encoder import MessageData

from queuebridge.codec import decode_wire, encode

_installed = False


class QueuebridgeEncoder(JSONEncoder):
    def encode(self, data: MessageData) -> bytes:
        payload = dict(data)
        for key in ("args", "kwargs"):
            if key in payload:
                payload[key] = encode(payload[key])
        return super().encode(payload)

    def decode(self, data: bytes) -> MessageData:
        raw = super().decode(data)
        payload = dict(raw)
        for key in ("args", "kwargs"):
            if key in payload:
                payload[key] = decode_wire(payload[key])
        return payload


def register_queuebridge(broker: dramatiq.Broker | None = None) -> None:
    """Install QueuebridgeEncoder globally. Idempotent."""
    global _installed
    if _installed:
        if broker is not None:
            dramatiq.set_broker(broker)
        return

    dramatiq.set_encoder(QueuebridgeEncoder())
    if broker is not None:
        dramatiq.set_broker(broker)
    _installed = True
