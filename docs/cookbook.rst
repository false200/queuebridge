Cookbook
========

Practical recipes for common queuebridge patterns.

Nested models and collections
------------------------------

queuebridge encodes nested structures recursively:

.. code-block:: python

   from uuid import uuid4
   from pydantic import BaseModel

   class LineItem(BaseModel):
       sku: str
       qty: int

   class Order(BaseModel):
       id: int
       items: list[LineItem]
       tags: set[str]

   from queuebridge import encode, decode

   order = Order(id=1, items=[LineItem(sku="A", qty=2)], tags={"urgent"})
   wire = encode(order)
   restored = decode(wire, Order)
   assert restored == order

Use explicit hints for collections:

.. code-block:: python

   batch = decode(wire_list, list[Order])

Optional and Union fields
-------------------------

For ``Optional[OrderCreate]``, pass ``None`` or a model; decoding uses the hint.

For ``Union[OrderA, OrderB]``, prefer tagged envelopes on encode (default for models).
Decoding tries Pydantic discriminated unions first, then each union arm.

Testing Celery without a broker
-------------------------------

.. code-block:: python

   app.conf.update(
       task_always_eager=True,
       task_store_eager_result=True,
   )

   ar = my_task.delay(OrderCreate(id=1, sku="X"))
   result = typed_result(ar, OrderResult).get()

Testing Dramatiq with StubBroker
--------------------------------

.. code-block:: python

   from dramatiq import Worker
   from dramatiq.brokers.stub import StubBroker
   from queuebridge.dramatiq import register_queuebridge

   broker = StubBroker()
   register_queuebridge(broker)
   broker.declare_queue("default")

   worker = Worker(broker, worker_timeout=100)
   worker.start()
   try:
       my_actor.send(OrderCreate(id=1, sku="X"))
       broker.join("default", timeout=5000)
   finally:
       worker.stop()

Using encode/decode outside task queues
---------------------------------------

The codec works standalone for APIs, caches, or CLI tools:

.. code-block:: python

   from queuebridge import encode, decode

   payload = encode({"orders": [order1, order2]})
   # store payload in Redis, S3, etc.
   restored = decode(payload, dict[str, list[Order]])

Manual wire inspection
----------------------

.. code-block:: python

   from queuebridge.codec import is_qb_envelope, decode_wire

   wire = encode(OrderCreate(id=1, sku="A"))
   assert is_qb_envelope(wire)
   model = decode_wire(wire)  # no hint needed when tags are present

Shared models across services
-----------------------------

Ensure the same model class is importable wherever you decode:

1. Put models in a shared package (e.g. ``mycompany.schemas``)
2. Use identical class names and module paths on producer and worker
3. FQN in ``__qb__`` tags must resolve on both sides

If you rename or move models, in-flight messages with old FQNs will fail to decode.

FastAPI + Celery pattern
------------------------

See ``examples/celery_fastapi/app.py``:

1. FastAPI validates HTTP body into ``OrderCreate``
2. ``process_order.delay(order)`` enqueues the model
3. Poll endpoint uses ``typed_result(ar, OrderResult).get()``
4. Return ``result.model_dump()`` for JSON response

Arq client + worker checklist
-----------------------------

1. ``serialize, deserialize = get_serializer_pair()``
2. Set on ``WorkerSettings`` **and** ``create_pool(..., job_serializer=..., job_deserializer=...)``
3. Decorate tasks with ``@qb_task`` then ``@validate_call``
4. Use ``await typed_result(job, ReturnModel)`` when fetching results

Common errors
-------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Error
     - Fix
   * - ``TypeError: not JSON serializable``
     - Call ``register_queuebridge()`` on the Celery app
   * - Worker gets ``dict`` not model
     - Add ``pydantic=True`` to ``@app.task``
   * - ``.get()`` returns ``dict``
     - Use ``typed_result(ar, Model).get()``
   * - Arq ``pickle`` errors after adding queuebridge
     - Both sides must use custom serializers; drain old pickle jobs
   * - ``QueuebridgeDecodeError`` on FQN
     - Model module not importable on worker; check shared package layout

Smoke test script
-----------------

Run the full integration smoke test (no Redis):

.. code-block:: bash

   pip install "queuebridge[all]"
   python examples/smoke_test_complex.py
