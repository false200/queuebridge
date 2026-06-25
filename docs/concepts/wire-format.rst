Wire format
===========

queuebridge uses a **JSON-first** wire format with optional **type tags** for values that lose type information in JSON.

The ``__qb__`` envelope
-----------------------

Non-primitive values that need type information are wrapped like this:

.. code-block:: json

   {
     "__qb__": {
       "t": "myapp.models.OrderCreate",
       "v": 1,
       "d": {"id": 1, "sku": "ABC"}
     }
   }

.. list-table::
   :header-rows: 1

   * - Field
     - Meaning
   * - ``t``
     - Fully-qualified type name (module + class)
   * - ``v``
     - Wire format version (always ``1`` for now)
   * - ``d``
     - JSON-safe payload

Constants (Python)
------------------

.. code-block:: python

   from queuebridge.types import QB_TAG, QB_VERSION

   QB_TAG == "__qb__"
   QB_VERSION == 1

Types and their wire representation
-----------------------------------

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Python type
     - On the wire
     - Decoded via
   * - ``BaseModel``
     - ``__qb__`` envelope, ``d`` = ``model_dump(mode="json")``
     - ``model_validate`` or FQN import
   * - ``UUID``
     - ``__qb__`` with ``t: uuid.UUID``, ``d: "<uuid string>"``
     - ``UUID(d)``
   * - ``datetime``, ``date``, ``time``
     - ``__qb__`` with ISO string in ``d``
     - ``fromisoformat``
   * - ``Decimal``
     - ``__qb__`` with string in ``d``
     - ``Decimal(d)``
   * - ``Enum``
     - ``__qb__`` with enum FQN and value
     - Enum class lookup
   * - ``list``, ``tuple``, ``set``
     - JSON list (elements encoded recursively)
     - Hint-driven (``list[T]``, etc.)
   * - ``dict``
     - JSON object (keys coerced to str)
     - Hint-driven
   * - ``str``, ``int``, ``float``, ``bool``, ``null``
     - Pass through unchanged
     - Pass through

Encode and decode API
---------------------

.. code-block:: python

   from queuebridge import encode, decode

   wire = encode(my_model)
   restored = decode(wire, OrderCreate)

``decode_wire()`` unwraps all ``__qb__`` envelopes recursively without hints. Dramatiq uses this on incoming messages.

Celery note
-----------

The Celery serializer uses ``encode(..., tag_models=False)`` for compatibility with ``pydantic=True``. Models become plain dicts on the wire; UUID/datetime inside ``model_dump(mode="json")`` are already strings.

Arq note
--------

Job dicts are msgpack-encoded **after** ``encode()``, so the binary blob contains queuebridge-tagged JSON-compatible structures.
