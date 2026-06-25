Installation
============

Requirements
------------

* Python **3.10** or newer
* Pydantic **v2** (``>=2.5``)

From PyPI
---------

Core package (codec only, no queue dependencies):

.. code-block:: bash

   pip install queuebridge

With a task queue backend
-------------------------

Install the extra that matches your stack:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Extra
     - Installs
   * - ``queuebridge[celery]``
     - Celery 5.5+, Kombu
   * - ``queuebridge[dramatiq]``
     - Dramatiq 1.14+
   * - ``queuebridge[arq]``
     - Arq 0.25+, msgpack
   * - ``queuebridge[all]``
     - All of the above

Examples:

.. code-block:: bash

   pip install "queuebridge[celery]"
   pip install "queuebridge[dramatiq]"
   pip install "queuebridge[arq]"
   pip install "queuebridge[all]"

From source (development)
-------------------------

.. code-block:: bash

   git clone https://github.com/false200/queuebridge.git
   cd queuebridge
   pip install -e ".[all,dev]"

Verify the install
------------------

.. code-block:: python

   import queuebridge
   print(queuebridge.__version__)

For a full smoke test without Redis:

.. code-block:: bash

   python examples/smoke_test_complex.py

Optional: build the docs locally
--------------------------------

.. code-block:: bash

   pip install -e ".[docs]"
   cd docs
   make html

Open ``docs/_build/html/index.html`` in your browser.
