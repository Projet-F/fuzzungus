.. _callbacks:

Callbacks
=========

Callbacks function are some function that depends on majority to which protocol do we fuzz. They are used to manage a communication with a server.

For example, a callback function can be used in FTP, to switch the port in the communication.

Firstly and due to the dependencies of the fuzzed protocol, these functions are declared in differents Class in the callback folder and inherit of the :class:`BaseCallback`. They can be used at the beginning of a test case: :meth:`pre_send` or after the fuzzed node (end of test case) : :meth:`post_send`. They can also be called between 2 :class:`Requests` by using the :meth:`Request.connect(request1,request2,callback_function)`.

How to define it ?
------------------
First, define the callback name Class:

.. code-block:: python

    class MyCallbackClass(BaseCallback):

then define your functions in that class

These functions have to follow the prototype:

.. code-block:: python

    def callback_exemple(self, target, fuzz_data_logger, session, *args, **kwargs):

How to use it ?
---------------

Firstly we have to add our callback module to `boofuzz/__init__.py` :

.. code-block:: python 
    
    from .myfilename import MyCallbackClass

and add it to `__all__`

then, add it to `boofuzz/__init__.py`

.. code-block:: python 

    from .callbacks import(MyCallbackClass)

then in `__all__`.

In the session definition, we define which Callback class that we are going to use:

.. code-block:: python 

    callback_module = MyCallbackClass

Then, you can call it in the session definition with:

.. code-block:: python 

    self.cb.callback_exemple


Example
-------

I want to fuzz a TFTP server, I send first a write request on the port 69. The server is replying an ACK with an other port than the port 69 and then i have to send data on this specific port.

First i will define my callback function.


.. code-block:: python

    def control_to_data(self, target, fuzz_data_logger, session, *args, **kwargs):
        #First target is bind to the port 69 so let's use an other one
        session.target_to_use = 1
        #We get the connection attribute form the both targets (an UDP socket there)
        connection_target0 = session.targets[0].get_connection()
        connection_target1 = session.targets[1].get_connection()
        #And we force the second target to use the same port as the first one for sending
        connection_target1.use_same_port(connection_target0)
        #We now bind the second target to the port who has been used by the server
        connection_target1.port = connection_target0.get_udp_client_port()[1]
        #Finnaly, we open the connection
        session.targets[session.target_to_use].open()

Now, in my tftp_example.py, when I connect the write request to the data node, I specify this function.

.. code-block:: python 

    connect(wrq,data,callback=self.cb.control_to_data)

Change `Default value` during a fuzzing session
-----------------------------------------------

In the case, you have to change a default value during a session depending of last reply you received, you can for example do that:

`session.nodes[1].stack[2]._default_value=session.last_recv[4:6]`

That fix the new default value of the 1st node, 2nd field to the value that we received last. 

