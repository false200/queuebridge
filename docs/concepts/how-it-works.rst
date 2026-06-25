How it works
============

queuebridge has two layers:

1. **Codec** (``queuebridge.codec``): encode/decode Python values to a JSON-safe wire format.
2. **Backend adapters**: plug the codec into Celery, Dramatiq, or Arq.

.. code-block:: text

   Your app                queuebridge              Task queue
   --------                -----------              ----------
   OrderCreate model  -->  encode()           -->   JSON / msgpack on wire
                           __qb__ tags

   Worker task        <--  decode + hints    <--   wire dict
   receives model

The flow (Celery example)
-------------------------

1. **Producer**: ``process_order.delay(OrderCreate(...))``
2. **Serializer**: Kombu calls ``queuebridge.encode()`` on the message body.
3. **Broker**: JSON bytes travel over Redis/RabbitMQ.
4. **Worker**: Celery ``pydantic=True`` validates kwargs dicts into models.
5. **Return**: Worker returns ``OrderResult``; Celery dumps to dict; codec encodes for result backend.
6. **Client**: ``typed_result(ar, OrderResult).get()`` decodes to a model.

What each backend does
----------------------

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Backend
     - Encode hook
     - Decode hook
   * - Celery
     - Kombu ``queuebridge-json`` serializer
     - Worker ``pydantic=True``; client uses ``typed_result``
   * - Dramatiq
     - ``QueuebridgeEncoder.encode()``
     - ``QueuebridgeEncoder.decode()`` + ``validate_call``
   * - Arq
     - msgpack + ``encode()``
     - ``@qb_task`` + ``validate_call``

Type hints matter
-----------------

Decoding uses your function annotations via ``typing.get_type_hints`` and Pydantic's ``TypeAdapter``.

If the wire value is a plain dict and your parameter is ``order: OrderCreate``, queuebridge calls ``OrderCreate.model_validate(dict)``.

If the wire value has a ``__qb__`` tag, the tag's type name is used to reconstruct the object.

See :doc:`wire-format` for tag details.

When you do not need tags
-------------------------

If you always pass type hints and use plain ``model_dump()`` dicts, decoding still works. Tags help when:

* The type is ambiguous (``Union``, ``Any``)
* You have nested UUID/datetime outside a model
* You decode without a concrete hint
