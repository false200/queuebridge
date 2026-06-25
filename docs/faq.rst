FAQ
===

Can I use Pydantic v1?
----------------------

No. queuebridge requires Pydantic v2 (``>=2.5``).

Do I still need ``pydantic=True`` on Celery tasks?
---------------------------------------------------

Strongly recommended. queuebridge serializes models on enqueue; ``pydantic=True`` validates them on the worker. They solve different problems.

Can I pass ``model_dump()`` dicts instead of models?
----------------------------------------------------

Yes. The worker still validates with ``pydantic=True``. Passing models directly is preferred because nested UUID/datetime types are handled consistently.

Why does ``ar.get()`` return a dict?
------------------------------------

Celery does not know your return type on the client. Use:

.. code-block:: python

   typed_result(ar, OrderResult).get()

Will you monkey-patch ``AsyncResult.get()``?
--------------------------------------------

No. Global patching is unsafe in apps with multiple Celery apps or mixed code. ``typed_result()`` is explicit and type-safe.

Does queuebridge work with ``shared_task``?
-------------------------------------------

Yes. Call ``register_queuebridge(app)`` on each Celery app instance you use.

What about task chords and chains?
----------------------------------

Not officially supported in v0.1. Nested signatures may need manual encoding in edge cases. Chord/chain support is on the roadmap.

Can I use pickle?
-----------------

Not as the default wire format. Pickle is out of scope for v0.1. An optional extra may be added later.

How do I test without Redis?
----------------------------

* **Celery**: ``task_always_eager=True``
* **Dramatiq**: ``StubBroker`` + ``Worker``
* **Script**: ``examples/smoke_test_complex.py``

How do I publish a new version?
-------------------------------

1. Bump ``version`` in ``pyproject.toml`` and ``queuebridge.__version__``
2. Tag ``v0.x.x`` and push
3. GitHub Actions publishes to PyPI (trusted publishing)

Where is the documentation hosted?
----------------------------------

Build locally with ``pip install -e ".[docs]" && cd docs && make html``.

Host on `Read the Docs <https://readthedocs.org/>`_ using the included ``.readthedocs.yaml``.
