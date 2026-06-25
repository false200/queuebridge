Dramatiq tutorial
=================

Dramatiq uses a global encoder to serialize messages. queuebridge replaces it with one that handles Pydantic models and other types.

Step 1: Install
---------------

.. code-block:: bash

   pip install "queuebridge[dramatiq]"

Step 2: Register before defining actors
---------------------------------------

Call ``register_queuebridge()`` at process startup, **before** ``@dramatiq.actor`` decorators run:

.. code-block:: python

   import dramatiq
   from dramatiq.brokers.redis import RedisBroker
   from queuebridge.dramatiq import register_queuebridge

   broker = RedisBroker()
   dramatiq.set_broker(broker)
   register_queuebridge()

Step 3: Use validate_call on your actor
---------------------------------------

Wire kwargs arrive as dicts with ``__qb__`` tags. Dramatiq's decoder unwraps them; ``validate_call`` coerces to your model:

.. code-block:: python

   from pydantic import BaseModel, validate_call

   class OrderCreate(BaseModel):
       id: int
       sku: str

   @dramatiq.actor
   @validate_call
   def process(order: OrderCreate):
       print(order.sku)

Decorator order matters: ``@dramatiq.actor`` on the outside, ``@validate_call`` inside (closer to the function).

Step 4: Send a model
--------------------

.. code-block:: python

   process.send(OrderCreate(id=1, sku="ABC"))

That is it. No ``model_dump()``.

How it works internally
-----------------------

``QueuebridgeEncoder`` subclasses Dramatiq's ``JSONEncoder``. On encode it runs ``queuebridge.encode()`` on ``args`` and ``kwargs``. On decode it runs ``decode_wire()`` so actors receive real Python objects.

Full example
------------

See ``examples/dramatiq_example/run.py``.

API reference
-------------

* :func:`queuebridge.dramatiq.register_queuebridge`
* :class:`queuebridge.dramatiq.encoder.QueuebridgeEncoder`
