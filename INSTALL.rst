Installing Fuzzungus
====================

Install with docker
-------------------

To build the docker image use the shell script ``./build.sh``.

After that, launch the two dockers (one for fuzzungus and the other for the database).
  ``docker compose up -d``

When the docker is up, you can access the documentation of this project.
Open `html_docs/index.html`.

Then, use boo to run the fuzzer :
  ``./boo --help``

  ``./boo fuzz --help``

Prerequisites
-------------

Fuzzungus requires Python >= 3.12. As a base requirement, the following packages are needed:

Ubuntu/Debian
  ``sudo apt-get install python3-pip python3-venv build-essential postgresql``
OpenSuse
  ``sudo zypper install python3-devel gcc postgresql``
CentOS
  ``sudo yum install python3-devel gcc postgresql``

Install from source
-------------------

It is strongly recommended to set up Fuzzungus in a `virtual environment (venv) <https://docs.python.org/3/tutorial/venv.html>`_.
First, clone the project in a directory that will hold the fuzzungus install:

.. code-block:: bash

    $ git clone https://git-pi-25.esisar.grenoble-inp.fr/pi25/fuzzungus.git && cd fuzzungus
    $ python3 -m venv env

This creates a new virtual environment env in the current folder. Note that the Python version in a virtual environment is fixed and chosen at its creation.
Unlike global installs, within a virtual environment ``python`` is aliased to the Python version of the virtual environment.

Next, add the path to the `boofuzz` folder in `env/bin/activate` : 

.. code-block:: bash

    PYTHONPATH="${PYTHONPATH}:/absolute/path/to/boofuzz"
    export PYTHONPATH

This is to ensure that the boofuzz package is available everywhere in the virtual environment.

Next, activate the virtual environment:

.. code-block:: bash

    $ source env/bin/activate

You can check that the variable has been set correctly by running:

.. code-block:: bash

    $ echo $PYTHONPATH

Ensure you have the latest version of both ``pip`` and ``setuptools``:

.. code-block:: bash

    (env) $ pip install -U pip setuptools

Then, install the necessary packages :

.. code-block:: bash

    (env) $ pip install attrs click colorama Flask funcy psutil pydot pyserial tornado deprecated psycopg websocket-client

Docs extras packages :

.. code-block:: bash

    (env) $ pip install poetry sphinx sphinx_rtd_theme sphinx_collapse sphinx-mermaid pygments graphviz

Dev extras packages :

.. code-block:: bash

    (env) $ pip install black flake8 ipaddress mock netifaces pygments pytest pytest-bdd pytest-cov poetry sphinx sphinx_rtd_theme sphinx_collapse sphinx-mermaid tox wheel graphviz

Finally, install the submodules. Currently, only `Seclist`_ is used.

.. code-block:: bash

    (env) $ git submodule init
    (env) $ git submodule update

.. warning::
    This may take up two minutes !

To run and test your fuzzing scripts, make sure to always activate the virtual environment beforehand.

.. note::
    To use the Postgres database with a source installation, use ``docker compose up db -d`` to launch only the db docker.

Extras
------

process\_monitor.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The process monitor is a tool for detecting crashes and restarting an application on Windows or Linux. While boofuzz
typically runs on a different machine than the target, the process monitor must run on the target machine itself.

network\_monitor.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The network monitor was Sulley’s primary tool for recording test data,
and has been replaced with boofuzz’s logging mechanisms.
However, some people still prefer the PCAP approach.

.. note::
    The network monitor requires Pcapy and Impacket, which will not be automatically installed with boofuzz. You can
    manually install them with ``pip install pcapy impacket``.

    If you run into errors, check out the Pcapy requirements on the `project page <https://github.com/helpsystems/pcapy>`_.

.. _help site: http://www.howtogeek.com/197947/how-to-install-python-on-windows/
.. _releases page: https://github.com/jtpereyda/boofuzz/releases
.. _`https://github.com/jtpereyda/boofuzz`: https://github.com/jtpereyda/boofuzz
.. _`Seclist`: https://github.com/danielmiessler/SecLists
