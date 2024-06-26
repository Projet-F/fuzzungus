.. _protocol-overview:

Protocol Overview
===================

See the :ref:`Quickstart <quickstart>` guide for an intro to using Fuzzungus in general and a basic protocol definition
example.

Overview
--------

Requests are messages, Blocks are chunks within a message, and Primitives are the elements (bytes, strings, numbers,
checksums, etc.) that make up a Block/Request.

Example
-------
Here is an example of an HTTP message. It demonstrates how to use Request, Block, and several primitives:

.. code-block:: python

    req = Request("HTTP-Request",children=(
        Block("Request-Line", children=(
            Group("Method", values= ["GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE"]),
            Delim("space-1", " "),
            String("URI", "/index.html"),
            Delim("space-2", " "),
            String("HTTP-Version", "HTTP/1.1"),
            Static("CRLF", "\r\n"),
        )),
        Block("Host-Line", children=(
            String("Host-Key", "Host:"),
            Delim("space", " "),
            String("Host-Value", "example.com"),
            Static("CRLF", "\r\n"),
        )),
        Static("CRLF", "\r\n"),
    ))

.. _custom-blocks:

Making Your Own Block/Primitive
-------------------------------

To make your own block/primitive:

1. Create an object that inherits from :class:`Fuzzable <boofuzz.Fuzzable>` or :class:`FuzzableBlock <boofuzz.FuzzableBlock>`
2. Override :meth:`mutations <boofuzz.Fuzzable.mutations>` and/or :meth:`encode <boofuzz.Fuzzable.encode>`.
3. Add it to the  `_init.py_` files : 
    - In the `primitives` or `blocks` folder :  
        - Import it : `from .$primitiveName import $PrimitiveName`
        - Add it in the `__all__` table

    - In the `boofuzz` folder : 
        - In the `from .primitives import ()`
        - In the `__all__` table as `$PrimitiveName`

If your block depends on references to other blocks, the way a checksum or length field depends on other parts of the
message, see the :class:`Size <boofuzz.Size>` source code for an example of how to avoid recursion issues, and Be
Careful. :)

.. autoclass:: boofuzz.Fuzzable
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: boofuzz.FuzzableBlock
    :members:
    :undoc-members:
    :show-inheritance:

Flagging blocks/primitives as depreciated
-----------------------------------------

Depending of Fuzzungus evolution, you may need to flag some blocks/primitives as depreciated. To do so, here are two methods.

First method with the `warnings` package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import warnings
    warnings.warn('setDaemon() is deprecated, set the daemon attribute instead',DeprecationWarning, stacklevel=2)

Second method with the `deprecated` package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from deprecated import deprecated
    @deprecated(version='x.x.x', reason="Use YourClass instead")

See `Deprecated - PyPi <https://pypi.org/project/Deprecated/>`_.