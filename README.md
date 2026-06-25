# queuebridge

**Pass Pydantic models to `.delay()` / `.send()` / `enqueue_job()` — get models back from results.**

Bidirectional Pydantic typing for [Celery](https://docs.celeryq.dev/), [Dramatiq](https://dramatiq.io/), and [Arq](https://arq-docs.helpmanual.io/) with one shared wire codec.

## The problem

Celery 5.5+ added `pydantic=True`, but it only validates on the **worker**:

- Callers must still `model_dump()` before `.delay()` — passing a model raises `TypeError: Object of type X is not JSON serializable` ([celery#9442](https://github.com/celery/celery/issues/9442))
- `.get()` returns a `dict`, not your model

Dramatiq's default JSON encoder fails on models, UUIDs, and datetimes ([dramatiq#660](https://github.com/Bogdanp/dramatiq/issues/660)).

Arq defaults to pickle with no Pydantic story ([arq#497](https://github.com/python-arq/arq/issues/497)).

```
Producer                    Worker                      Client
────────                    ──────                      ──────
.delay(model)  ──X──>      pydantic=True validates     .get() → dict
(model_dump() required)     args on worker only
```

**queuebridge** fixes the producer side and client-side result decoding with a shared `__qb__` tagged wire format.

## Install

```bash
pip install queuebridge[celery]     # Celery + Kombu
pip install queuebridge[dramatiq]   # Dramatiq
pip install queuebridge[arq]        # Arq + msgpack
pip install queuebridge[all]        # everything
```

## Quickstart

### Celery

```python
from celery import Celery
from queuebridge.celery import register_queuebridge, typed_result
from myapp.models import OrderCreate, OrderResult

app = Celery("orders", broker="redis://localhost:6379/0")
register_queuebridge(app)

@app.task(pydantic=True)
def process_order(order: OrderCreate) -> OrderResult:
    return OrderResult(id=order.id, status="processed")

# Enqueue with a model directly
ar = process_order.delay(OrderCreate(id=1, sku="ABC"))

# Get a model back (not a dict)
result = typed_result(ar, OrderResult).get(timeout=10)
```

> **Note:** Celery cannot safely monkey-patch `AsyncResult.get()` globally. Use `typed_result()` for typed client results.

### Dramatiq

```python
import dramatiq
from pydantic import validate_call
from queuebridge.dramatiq import register_queuebridge
from myapp.models import OrderCreate

register_queuebridge()

@dramatiq.actor
@validate_call
def process(order: OrderCreate):
    print(order)

process.send(OrderCreate(id=1, sku="ABC"))
```

### Arq

```python
from arq.connections import RedisSettings
from pydantic import validate_call
from queuebridge.arq import get_serializer_pair, qb_task, typed_result
from myapp.models import OrderCreate, OrderResult

serialize, deserialize = get_serializer_pair()

@qb_task
@validate_call
async def process_order(ctx, order: OrderCreate) -> OrderResult:
    return OrderResult(id=order.id, status="ok")

class WorkerSettings:
    functions = [process_order]
    redis_settings = RedisSettings()
    job_serializer = serialize
    job_deserializer = deserialize
```

## Wire format

Non-JSON-native values are wrapped in a tagged envelope:

```json
{
  "__qb__": {
    "t": "myapp.models.OrderCreate",
    "v": 1,
    "d": {"id": 1, "sku": "ABC"}
  }
}
```

Decode uses function type hints (`TypeAdapter`) when tags are absent — a plain dict + `OrderCreate` hint still validates.

## Security

Deserialization resolves types by fully-qualified name (`import_fqn`). **Only deserialize from brokers you trust.** Module allowlisting is planned for v0.2.

## Comparison

| Solution | Celery | Dramatiq | Arq | Bidirectional `.get()` |
|----------|--------|----------|-----|------------------------|
| Celery `pydantic=True` | worker only | — | — | no |
| Blog / msgpack hacks | partial | partial | partial | varies |
| **queuebridge** | yes | yes | yes | yes (`typed_result`) |

## Roadmap

- `allowed_modules` security filter on `register_queuebridge()`
- Optional pickle extra
- Chord / chain signature support

## License

MIT
