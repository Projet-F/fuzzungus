.. _logging:

=======
Logging
=======

Boofuzz provides flexible logging. All logging classes implement :class:`IFuzzLogger <boofuzz.IFuzzLogger>`.
Built-in logging classes are detailed below.

To use multiple loggers at once, see :class:`FuzzLogger <boofuzz.FuzzLogger>`.

To edit logging styling, see the :file:`helpers.py` and :file:`boofuzz.css` files. 

Fuzzing Levels
--------------

Fuzzungus now supports multiple levels of logging for the CLI : 

.. list-table::
   :header-rows: 1

   * - Log level
     - Description
     - CLI option
   * - 0
     - Print on the same line the "open test case" log and also print fail, error and target-error.
     - Default
   * - 1
     - Same as log level 0 but do not print on the same line.
     - `-v`
   * - 2
     - Log level 1 + check, pass, info and target-warn.
     - `-vv`
   * - 3
     - Most verbose level : log level 2 + open test step, receive and send.
     - `-vvv`

Logging Interface (IFuzzLogger)
-------------------------------

.. autoclass:: boofuzz.IFuzzLogger
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: boofuzz.IFuzzLoggerBackend
    :members:
    :undoc-members:
    :show-inheritance:

Postgres Logging
----------------

.. note::
  To use this method of logging, the Postgres database have to be  running.
  Fuzzungus use docker to achieve that. Use ``docker compose up db -d`` to achieve that.

Each campaign create a different database. The name of the databases are the id of each campaign, so it's easy to find which database is for each campaign.

In each database, there are at least two tables : `steps` and `cases`.

Furthermore, a replay creates two other tables in the same database of the original campaign : steps and cases ones but prefix with date and time.

Do ``./boo db list`` to see all databases which their size.

And, inside a database (in a Postgres shell), type ``\d+`` to list all tables.

.. autoclass:: boofuzz.FuzzLoggerPostgres
    :members:
    :undoc-members:
    :show-inheritance:

Text Logging
------------

.. note::
  The Text Logger now uses one more logger, `log-recap`, to print the recap of the fuzzing session when a `SIGINT` is received.

.. autoclass:: boofuzz.FuzzLoggerText
    :members:
    :undoc-members:
    :show-inheritance:

Db Logging
----------

.. deprecated:: 1.0
  Deprecated if favor of :class:`FuzzLoggerPostgres <boofuzz.FuzzLoggerPostgres>`
  This is the old way to log in a db : sqlite database file.

.. autoclass:: boofuzz.FuzzLoggerDb
    :members:
    :undoc-members:
    :show-inheritance:

CSV Logging
-----------

.. autoclass:: boofuzz.FuzzLoggerCsv
    :members:
    :undoc-members:
    :show-inheritance:

Console-GUI Logging
-------------------

.. autoclass:: boofuzz.FuzzLoggerCurses
    :members:
    :undoc-members:
    :show-inheritance:

FuzzLogger Object
-----------------

.. autoclass:: boofuzz.FuzzLogger
    :members:
    :undoc-members:
    :show-inheritance:
