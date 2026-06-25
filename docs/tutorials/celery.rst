Celery tutorial
===============

This guide walks through Celery from scratch. No prior queuebridge knowledge required.

Step 1: Install
---------------

.. code-block:: bash

   pip install "queuebridge[celery]"

You also need a broker (Redis is common):

.. code-block:: bash

   pip install redis

Step 2: Define your models
--------------------------

Use standard Pydantic v2 models:

.. code-block:: python

   from pydantic import BaseModel, Field

   class OrderCreate(BaseModel):
       id: int
       sku: str = Field(min_length=1)

   class OrderResult(BaseModel):
       id: int
       status: str

Step 3: Create the Celery app and register queuebridge
------------------------------------------------------

Call ``register_queuebridge()`` **once** when your app starts (worker and producer):

.. code-block:: python

   from celery import Celery
   from queuebridge.celery import register_queuebridge

   celery_app = Celery(
       "orders",
       broker="redis://localhost:6379/0",
       backend="redis://localhost:6379/0",
   )
   register_queuebridge(celery_app)

This registers a Kombu serializer named ``queuebridge-json`` and sets it as the default task and result serializer.

Step 4: Write your task
-----------------------

Use ``pydantic=True`` so Celery validates arguments on the worker:

.. code-block:: python

   @celery_app.task(pydantic=True)
   def process_order(order: OrderCreate) -> OrderResult:
       assert isinstance(order, OrderCreate)
       return OrderResult(id=order.id, status="processed")

Step 5: Enqueue with a model
----------------------------

Before queuebridge you had to write:

.. code-block:: python

   process_order.delay(order.model_dump())  # old way

Now pass the model directly:

.. code-block:: python

   process_order.delay(OrderCreate(id=1, sku="ABC"))

Step 6: Get a typed result
--------------------------

Celery's ``AsyncResult.get()`` still returns a ``dict``. Use ``typed_result()``:

.. code-block:: python

   from queuebridge.celery import typed_result

   ar = process_order.delay(OrderCreate(id=1, sku="ABC"))
   result = typed_result(ar, OrderResult).get(timeout=10)

   assert isinstance(result, OrderResult)
   print(result.status)

``typed_result`` wraps the async result and proxies attributes like ``.id``, ``.state``, and ``.ready()``.

Full example
------------

See ``examples/celery_fastapi/`` in the repository for a FastAPI app that enqueues orders and polls typed results.

Testing without Redis
---------------------

Use eager mode in tests:

.. code-block:: python

   celery_app.conf.update(
       task_always_eager=True,
       task_store_eager_result=True,
   )

Common mistakes
---------------

**Forgot ``register_queuebridge``**

``delay(model)`` raises ``TypeError: Object of type X is not JSON serializable``.

**Forgot ``pydantic=True``**

The worker receives a plain dict instead of a validated model.

**Using ``ar.get()`` instead of ``typed_result``**

You get a dict back, not a Pydantic model. That is expected; use ``typed_result`` on the client.

API reference
-------------

* :func:`queuebridge.celery.register_queuebridge`
* :func:`queuebridge.celery.typed_result`
* :class:`queuebridge.celery.result.TypedAsyncResult`
