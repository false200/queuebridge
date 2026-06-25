Arq tutorial
============

Arq defaults to **pickle**, which is fast but opaque and unsafe with untrusted data. queuebridge provides **msgpack** serializers that understand Pydantic models.

Step 1: Install
---------------

.. code-block:: bash

   pip install "queuebridge[arq]"

Step 2: Get the serializer pair
-------------------------------

.. code-block:: python

   from queuebridge.arq import get_serializer_pair

   serialize, deserialize = get_serializer_pair()

Step 3: Configure worker and client
-----------------------------------

**Both** the Arq worker and ``create_pool()`` must use the same serializers:

.. code-block:: python

   from arq.connections import RedisSettings

   class WorkerSettings:
       functions = [process_order]
       redis_settings = RedisSettings()
       job_serializer = serialize
       job_deserializer = deserialize

When enqueueing from your app:

.. code-block:: python

   pool = await create_pool(
       RedisSettings(),
       job_serializer=serialize,
       job_deserializer=deserialize,
   )

Step 4: Decorate your task with qb_task
---------------------------------------

Arq passes wire dicts into your function. ``@qb_task`` decodes them using your type hints:

.. code-block:: python

   from pydantic import BaseModel, validate_call
   from queuebridge.arq import qb_task

   class OrderCreate(BaseModel):
       id: int
       sku: str

   @qb_task
   @validate_call
   async def process_order(ctx, order: OrderCreate) -> OrderResult:
       return OrderResult(id=order.id, status="ok")

Apply ``@qb_task`` **outside** ``@validate_call``.

Step 5: Typed job results
-------------------------

.. code-block:: python

   from queuebridge.arq import typed_result

   job = await pool.enqueue_job("process_order", order=OrderCreate(id=1, sku="X"))
   result = await typed_result(job, OrderResult)

Full example
------------

See ``examples/arq_example/worker.py``.

API reference
-------------

* :func:`queuebridge.arq.get_serializer_pair`
* :func:`queuebridge.arq.qb_task`
* :func:`queuebridge.arq.typed_result`
