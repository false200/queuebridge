queuebridge
===========

**Bidirectional Pydantic serialization for Celery, Dramatiq, and Arq.**

Pass Pydantic models to ``.delay()``, ``.send()``, or ``enqueue_job()``. Get models back from results. One shared wire codec powers every backend.

.. image:: https://img.shields.io/pypi/v/queuebridge.svg
   :target: https://pypi.org/project/queuebridge/
   :alt: PyPI version

.. image:: https://img.shields.io/badge/python-3.10%2B-blue.svg
   :target: https://pypi.org/project/queuebridge/
   :alt: Python 3.10+

.. image:: https://github.com/false200/queuebridge/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/false200/queuebridge/actions/workflows/ci.yml
   :alt: CI

----

**New here?** Start with :doc:`getting-started`, then pick your backend tutorial:

* :doc:`tutorials/celery`
* :doc:`tutorials/dramatiq`
* :doc:`tutorials/arq`

----

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Start here

   getting-started
   installation

.. toctree::
   :maxdepth: 2
   :caption: Tutorials (by backend)

   tutorials/celery
   tutorials/dramatiq
   tutorials/arq

.. toctree::
   :maxdepth: 2
   :caption: Concepts

   concepts/how-it-works
   concepts/wire-format
   concepts/why-not-celery-pydantic

.. toctree::
   :maxdepth: 2
   :caption: Reference

   api/index
   cookbook
   security
   faq

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
