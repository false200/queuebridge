Security
========

Trusted brokers only
--------------------

queuebridge decodes wire data by **importing Python types from fully-qualified names** (``import_fqn``). A malicious message could reference arbitrary importable classes.

**Only connect to brokers and result backends you trust.**

Do not expose your Redis/RabbitMQ ports to the public internet without authentication.

What gets imported
------------------

When a ``__qb__`` envelope is decoded, queuebridge:

1. Reads the ``t`` field (e.g. ``myapp.models.OrderCreate``)
2. Imports the module and resolves the class
3. Calls ``model_validate`` or equivalent

If an attacker can enqueue jobs, they could craft envelopes pointing at unexpected types.

Mitigations today
-----------------

* Run workers in isolated networks
* Use broker authentication (Redis ACLs, RabbitMQ users)
* Treat task queues like internal APIs

Planned for v0.2
----------------

``ALLOWED_MODULE_PREFIXES`` in ``queuebridge.types`` will let you restrict imports:

.. code-block:: python

   # future API sketch
   register_queuebridge(app, allowed_modules=("myapp.",))

Today the tuple is empty, meaning all modules are allowed.

Pickle vs msgpack (Arq)
-----------------------

Arq defaults to pickle, which can execute arbitrary code during deserialization. queuebridge's Arq adapter uses **msgpack** plus the ``__qb__`` codec instead. Still only use with trusted producers.

Reporting issues
----------------

Report security concerns via `GitHub Issues <https://github.com/false200/queuebridge/issues>`_.
