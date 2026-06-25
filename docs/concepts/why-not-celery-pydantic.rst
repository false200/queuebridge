Why not Celery pydantic=True alone?
====================================

Celery 5.5+ supports ``@app.task(pydantic=True)``. That is useful, but it only covers **half** the story.

What pydantic=True does
-----------------------

On the **worker**, Celery:

* Converts kwargs dicts into Pydantic models using your annotations
* Dumps return models to dicts via ``model_dump()`` for the result backend

What it does not do
-------------------

On the **producer** (your API, CLI, or script calling ``.delay()``):

* You must still serialize models yourself
* Passing ``OrderCreate(...)`` directly raises ``TypeError: not JSON serializable`

On the **client** (calling ``.get()``):

* You receive a **dict**, not your return model

Official docs quote
-------------------

From the `Celery task documentation <https://docs.celeryq.dev/en/stable/userguide/tasks.html#argument-validation-with-pydantic>`_:

   Argument validation only covers arguments/return values on the task side.
   You still have serialize arguments yourself when invoking a task with
   delay() or apply_async().

Community reports
-----------------

* `celery#9442 <https://github.com/celery/celery/issues/9442>`_ - models not serializable on enqueue
* `dramatiq#660 <https://github.com/Bogdanp/dramatiq/issues/660>`_ - JSON encoder fails on models
* `arq#497 <https://github.com/python-arq/arq/issues/497>`_ - request for native Pydantic support

What queuebridge adds
---------------------

.. list-table::
   :header-rows: 1

   * - Stage
     - Celery alone
     - With queuebridge
   * - ``.delay(model)``
     - Fails or needs ``model_dump()``
     - Works
   * - Worker receives
     - Model (with pydantic=True)
     - Model (with pydantic=True)
   * - ``.get()`` returns
     - ``dict``
     - ``dict`` (use ``typed_result`` for model)

queuebridge does not replace Celery's worker validation. It complements it by fixing producer serialization and offering client-side typed results.
