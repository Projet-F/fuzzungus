.. _connections:

===========
Connections
===========

Connection objects implement :class:`ITargetConnection <boofuzz.connections.ITargetConnection>`.
Available options include:

- :class:`TCPSocketConnection <boofuzz.connections.TCPSocketConnection>`
- :class:`UDPSocketConnection <boofuzz.connections.UDPSocketConnection>`
- :class:`SSLSocketConnection <boofuzz.connections.SSLSocketConnection>`
- :class:`RawL2SocketConnection <boofuzz.connections.RawL2SocketConnection>`
- :class:`RawL3SocketConnection <boofuzz.connections.RawL3SocketConnection>`
- :func:`SocketConnection (depreciated)<boofuzz.connections.SocketConnection>`
- :class:`SerialConnection <boofuzz.connections.SerialConnection>`
- :class:`WebSocketConnection <boofuzz.connections.WebSocketConnection>`

ITargetConnection
=================

ITargetConnection defines the interface used by the Target classes when sending
and receiving data. This represents the network layer or medium directly below
the protocol under test.

Design Considerations
---------------------

Design goals:

 1. Flexibility with mediums.
 2. Low-layer; avoid interactions with rest of framework.
    * Normal logging is left to higher layers.
 3. Facilitate thorough, auditable logs.
    * The send method returns the number of bytes actually transmitted, since some mediums have maximum transmission unit (MTU) limits.
    * The Sulley code using a connection should check this value and log the number of bytes transmitted.
    * This enables thorough auditability of data actually sent.

Source code
-----------

.. autoclass:: boofuzz.connections.ITargetConnection
    :members:
    :undoc-members:
    :show-inheritance:

BaseSocketConnection
====================

The SocketConnection is used by the Target class to encapsulate socket connection details. It implements ITargetConnection.

Multiple protocols may be used; see constructor.

Future
------

The low-level socket protocols have maximum transmission unit (MTU) limits
based on the standard ethernet frame. Availability of jumbo frames could
enable some interesting tests.

Source code
-----------

.. autoclass:: boofuzz.connections.BaseSocketConnection
    :members:
    :undoc-members:
    :show-inheritance:

TCPSocketConnection
===================
.. autoclass:: boofuzz.connections.TCPSocketConnection
    :members:
    :undoc-members:
    :show-inheritance:

UDPSocketConnection
===================
.. autoclass:: boofuzz.connections.UDPSocketConnection
    :members:
    :undoc-members:
    :show-inheritance:

SSLSocketConnection
===================
.. autoclass:: boofuzz.connections.SSLSocketConnection
    :members:
    :undoc-members:
    :show-inheritance:

RawL2SocketConnection
=====================
.. autoclass:: boofuzz.connections.RawL2SocketConnection
    :members:
    :undoc-members:
    :show-inheritance:

RawL3SocketConnection
=====================
.. autoclass:: boofuzz.connections.RawL3SocketConnection
    :members:
    :undoc-members:
    :show-inheritance:

SocketConnection
================
.. autofunction:: boofuzz.connections.SocketConnection

SerialConnection
================
.. autoclass:: boofuzz.connections.SerialConnection
    :members:
    :undoc-members:
    :show-inheritance:

WebSocketConnection
===================
.. autoclass:: boofuzz.connections.WebSocketConnection
    :members:
    :undoc-members:
    :show-inheritance: