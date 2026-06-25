# queuebridge

[![PyPI version](https://img.shields.io/pypi/v/queuebridge.svg)](https://pypi.org/project/queuebridge/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://pypi.org/project/queuebridge/)
[![CI](https://github.com/false200/queuebridge/actions/workflows/ci.yml/badge.svg)](https://github.com/false200/queuebridge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Bidirectional [Pydantic](https://docs.pydantic.dev/) serialization for [Celery](https://docs.celeryq.dev/), [Dramatiq](https://dramatiq.io/), and [Arq](https://arq-docs.helpmanual.io/). One shared wire codec: pass models on enqueue, get models back from results.

Celery 5.5+ `pydantic=True` only validates on the worker. Callers still `model_dump()` before `.delay()`, and `.get()` returns a `dict`. Dramatiq chokes on models and UUIDs. Arq defaults to pickle. **queuebridge** fixes all three with a thin codec + backend adapters.

## Install

```sh
pip install queuebridge
```

Extras:

```sh
pip install queuebridge[celery]     # Celery + Kombu
pip install queuebridge[dramatiq]   # Dramatiq
pip install queuebridge[arq]        # Arq + msgpack
pip install queuebridge[all]        # all backends
```

Requires **Python 3.10+** and **Pydantic v2**.

**Documentation:** https://queuebridge.readthedocs.io

## Usage

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

ar = process_order.delay(OrderCreate(id=1, sku="ABC"))
result = typed_result(ar, OrderResult).get(timeout=10)
```

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

## API

### `encode(value, *, tag_models=True)`

Recursively transform a Python value into a JSON-serializable structure.

#### value

*Required*  
Type: `Any`

The value to encode: Pydantic models, nested containers, `UUID`, `datetime`, `Decimal`, `Enum`, etc.

#### tag_models

Type: `boolean`  
Default: `true`

When `true`, `BaseModel` instances are wrapped in a `__qb__` envelope with a fully-qualified type name. When `false`, models are dumped with `model_dump(mode="json")` only.

```python
from queuebridge import encode, decode
from myapp.models import OrderCreate

wire = encode(OrderCreate(id=1, sku="ABC"))
restored = decode(wire, OrderCreate)
```

---

### `decode(value, hint=Any, *, strict=False)`

Recursively decode a wire value back to Python using an optional type hint.

#### value

*Required*  
Type: `Any`

Wire value: primitives, lists, dicts, or `__qb__` envelopes.

#### hint

Type: `Any`  
Default: `Any`

Type hint used for validation. `TypeAdapter(hint).validate_python()` is used when the hint is concrete.

#### strict

Type: `boolean`  
Default: `false`

When `true`, raise `QueuebridgeDecodeError` if the value cannot be decoded.

---

### `decode_wire(value)`

Recursively unwrap `__qb__` envelopes without type hints. Used internally by Dramatiq's decoder.

Type: `Any` -> `Any`

---

### `register_queuebridge(app, *, strict=False)` (Celery)

Register the `queuebridge-json` Kombu serializer on a Celery app. Idempotent: safe to call twice.

#### app

*Required*  
Type: `celery.Celery`

#### strict

Type: `boolean`  
Default: `false`

Reserved for future strict decode behavior.

Sets `task_serializer`, `result_serializer`, and `accept_content` on the app.

---

### `typed_result(async_result, return_type)` (Celery)

Wrap a Celery `AsyncResult` so `.get()` returns a Pydantic model instead of a `dict`.

#### async_result

*Required*  
Type: `celery.result.AsyncResult`

#### return_type

*Required*  
Type: `type[T]`

Returns `TypedAsyncResult[T]`, which proxies `.id`, `.state`, `.ready()`, etc.

> Celery cannot safely monkey-patch `AsyncResult.get()` globally. Use `typed_result()` on the client.

---

### `register_queuebridge(broker=None)` (Dramatiq)

Install `QueuebridgeEncoder` via `dramatiq.set_encoder()`. Call once at process startup.

#### broker

Type: `dramatiq.Broker | None`  
Default: `None`

If provided, also calls `dramatiq.set_broker(broker)`.

---

### `get_serializer_pair()` (Arq)

Returns `(serialize, deserialize)` callables for `job_serializer` / `job_deserializer`.

```python
serialize, deserialize = get_serializer_pair()
```

Uses **msgpack** over queuebridge-encoded dicts. Set on both `WorkerSettings` and `create_pool()`.

---

### `qb_task(fn)` (Arq)

Decorator that decodes wire args/kwargs using function type hints before your async task runs.

Apply **outside** `@validate_call`:

```python
@qb_task
@validate_call
async def process_order(ctx, order: OrderCreate) -> OrderResult:
    ...
```

---

### `typed_result(job, return_type)` (Arq)

```python
result = await typed_result(job, OrderResult)
```

Decode the `job.result()` payload into a Pydantic model.

## Wire format

Non-JSON-native values use a tagged envelope:

```json
{
  "__qb__": {
    "t": "myapp.models.OrderCreate",
    "v": 1,
    "d": {"id": 1, "sku": "ABC"}
  }
}
```

| Python type | Encode | Decode |
|-------------|--------|--------|
| `BaseModel` | envelope + `model_dump(mode="json")` | `model_validate` or FQN import |
| `UUID`, `datetime`, `Decimal`, `Enum` | tagged envelope | builtin dispatch |
| `list`, `dict`, `set`, `tuple` | recurse | recurse via hint |
| Primitives | pass through | pass through |

A plain `dict` + `OrderCreate` hint still validates. Tags are for ambiguity, not required when hints are known.

## Why not Celery `pydantic=True` alone?

```
Producer                    Worker                      Client
------                      ------                      ------
.delay(model)  FAIL>        pydantic=True validates     .get() -> dict
(model_dump() required)     args on worker only
```

- [celery#9442](https://github.com/celery/celery/issues/9442): models not JSON-serializable on enqueue
- [dramatiq#660](https://github.com/Bogdanp/dramatiq/issues/660): no Pydantic support
- [arq#497](https://github.com/python-arq/arq/issues/497): pickle default, Pydantic requested

## Comparison

| Solution | Celery | Dramatiq | Arq | Typed `.get()` |
|----------|--------|----------|-----|----------------|
| Celery `pydantic=True` | worker only | n/a | n/a | no |
| Blog / msgpack hacks | partial | partial | partial | varies |
| **queuebridge** | yes | yes | yes | yes |

## Security

Deserialization resolves types by fully-qualified name (`import_fqn`). **Only deserialize from brokers you trust.**

`ALLOWED_MODULE_PREFIXES` allowlisting is planned for v0.2.

## Examples

| Path | Description |
|------|-------------|
| [`examples/celery_fastapi/`](examples/celery_fastapi/) | FastAPI enqueue + typed result polling |
| [`examples/dramatiq_example/`](examples/dramatiq_example/) | Dramatiq + `validate_call` |
| [`examples/arq_example/`](examples/arq_example/) | Arq worker with custom serializers |
| [`examples/smoke_test_complex.py`](examples/smoke_test_complex.py) | End-to-end smoke test (no Redis) |
| [`pypi_verify/run_complex.py`](pypi_verify/run_complex.py) | PyPI install verification script |

## Related

- [Celery Pydantic docs](https://docs.celeryq.dev/en/stable/userguide/tasks.html#argument-validation-with-pydantic): worker-only validation
- [Arq custom serializers](https://arq-docs.helpmanual.io/#custom-job-serializers): msgpack hook point
- [Dramatiq encoders](https://dramatiq.io/advanced.html#custom-encoders): `set_encoder()` extension point

## License

MIT. See [LICENSE](LICENSE).

## Community

* [Contributing](CONTRIBUTING.md)
* [Code of Conduct](CODE_OF_CONDUCT.md)
* [Security policy](SECURITY.md)
* [Documentation](https://queuebridge.readthedocs.io)
