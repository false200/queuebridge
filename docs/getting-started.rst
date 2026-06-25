Getting started
===============

What is queuebridge?
--------------------

Task queues (Celery, Dramatiq, Arq) move data between processes as **serialized bytes** (usually JSON or pickle). Pydantic models are **not** JSON-serializable by default.

Most teams work around this by calling ``model_dump()`` before enqueue and manually rebuilding models after ``.get()``. That is tedious and easy to get wrong.

**queuebridge** is a small library that:

1. **Encodes** Python values (Pydantic models, UUID, datetime, nested lists, etc.) into a JSON-safe wire format.
2. **Decodes** wire data back to Python types using your function **type hints**.
3. **Plugs in** to each queue with a one-line setup call.

The same codec is used everywhere, so values round-trip consistently across backends.

What you need to know
---------------------

* **Python 3.10+**
* **Pydantic v2** (not v1)
* Basic familiarity with one task queue (Celery, Dramatiq, or Arq)

You do **not** need to understand the wire format to get started. Install, call ``register_queuebridge()``, pass models to your tasks.

The problem in 30 seconds
-------------------------

Celery 5.5 added ``pydantic=True``, but it only helps on the **worker**:

.. code-block:: text

   Producer                 Worker                    Client
   --------                 ------                    ------
   .delay(model)  FAIL      pydantic validates        .get() -> dict
   (need model_dump)        args on worker only

queuebridge fixes **enqueue** (producer) and **typed results** (client).

Minimal example (Celery)
------------------------

.. code-block:: python

   from celery import Celery
   from pydantic import BaseModel
   from queuebridge.celery import register_queuebridge, typed_result

   class Order(BaseModel):
       id: int
       sku: str

   class OrderResult(BaseModel):
       id: int
       status: str

   app = Celery("demo", broker="redis://localhost:6379/0")
   register_queuebridge(app)

   @app.task(pydantic=True)
   def process(order: Order) -> OrderResult:
       return OrderResult(id=order.id, status="ok")

   # Pass a model directly (no model_dump)
   ar = process.delay(Order(id=1, sku="ABC"))

   # Get a model back (not a dict)
   result = typed_result(ar, OrderResult).get(timeout=10)

Next steps
----------

1. :doc:`installation` - install the right extra for your backend
2. Pick a tutorial:

   * :doc:`tutorials/celery`
   * :doc:`tutorials/dramatiq`
   * :doc:`tutorials/arq`

3. Read :doc:`concepts/how-it-works` when you want the full picture
