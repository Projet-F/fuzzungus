.. _session-configuration:

Configuration of a session
==========================

In Fuzzungus, just like in Boofuzz, configuration files define a fuzzing session, not a protocol to fuzz.
The main difference here is that Boofuzz session configuration was quite basic, only giving examples of standalone scripts.
In Fuzzungus, we tried to normalize the configuration process, with three steps : 

1. Instead of standalone configuration scripts, we now have a :class:`BaseConfig`, from which every configuration file should enherit. That class creates and connect to the session and the targets in the backend through methods that shouldn't be overriden, and defines a number of parameters that can be fixed in a subclass.
2. Addition of a `main.py` file, that calls the configuration file and runs the session. This file is the one that should be run to start the fuzzing session. It also provides a useful number of CLI arguments.
3. Normalization of the callback process, that now enherit from the :class:`BaseCallback` class, or even from other callback classes, only overriding a few of the parent class' methods. For more information on callbacks, see :ref:`callbacks`.

Configuration files
-------------------

Let's take a look at how the :class:`BaseConfig` is made, and then at an example configuration file.

BaseConfig
^^^^^^^^^^

.. autoclass:: boofuzz.BaseConfig
    :members:
    :undoc-members:
    :show-inheritance:

Example configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^^

Here the example configuration file for TFTP overrides only some of the :class:`BaseConfig` parameters, letting some of them to their default values.

.. warning::
    For standardization purposes, the class name for every configuration module should always be :class:`Config`.
    This can be changed or improved in the module :mod:`boofuzz.BaseConfig`, if you want more flexibility.

.. literalinclude:: ../../configuration-files/tftp/tftp_advanced_demo.py

Nominal Data
------------

During fuzzing, you can use nominal data to check if the target is still alive.

In the campaign configuration file, you have two functions that perform these tests.

Define
^^^^^^

One is to define the nominal data :

.. code-block:: python

    def config_nominal(self) -> None:
        rrq = Request("rrq", children=(
            Static(name="opcode", default_value="\x00\x01"),
            Static(name="filename", default_value="nominal_test"),
            Static(name="null", default_value=b'\0'),
            Static(name="mode", default_value="octet"),
            Static(name="null2", default_value=b'\0'),
        ))
        self.session.set_nominal_data([rrq])

All primitives are :class:`Static` because they are not fuzz.

The function :func:`set_nominal_data` accept a table of nominal data to send. These data can be request with only :class:`Static` primitive or callback functions.

Example with FTP :

.. code-block:: python

    self.session.set_nominal_data([user, passw, cwd, pasv, callback.ParserPortPASV, type, ...])

Verify
^^^^^^

The other function is to verify that the target respond well to the nominal data :

.. code-block:: python

    @staticmethod
    def nominal_recv_test(session: Session) -> bool:
        expected_data = b'\x00\x03\x00\x01nominal_data\n'
        test = session.last_recv == expected_data
        if not test:
            session.get_fuzz_data_logger().log_info(f'Error in recv data (nominal test). The recv data should have been'
                                                    f'"{expected_data}"')
        return test

This function must return a boolean.

You can see the skeleton of these both functions in the :class:`BaseConfig` class.

Frequency
^^^^^^^^^

By default, this nominal test is perform every 50 test case, but this can be change.

.. code-block:: python

    nominal_test_interval: int = 50
