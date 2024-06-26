.. _monitors:

========
Monitors
========

Monitors are components that monitor the target for specific behaviour. A
monitor can be passive and just observe and provide data or behave more actively,
interacting directly with the target. Some monitors also have the capability to
start, stop and restart targets.

Detecting a crash or misbehaviour of your target can be a complex, non-straight
forward process depending on the tools you have available on your targets host;
this holds true especially for embedded devices. Fuzzungus provides three main
monitor implementations:

- :class:`ProcessMonitor <boofuzz.monitors.ProcessMonitor>`, a Monitor that collects debug info from process on Windows
  and Unix. It also can restart the target process and detect segfaults.
- :class:`NetworkMonitor <boofuzz.monitors.NetworkMonitor>`, a Monitor that passively captures network traffic via PCAP
  and attaches it to the testcase log.
- :class:`CallbackMonitor <boofuzz.monitors.CallbackMonitor>`, which is used to implement the callbacks that can be
  supplied to the Session class.
- :class:`BusyboxMonitor <boofuzz.monitors.BusyboxMonitor>`, a Monitor that collects debug info from process on Busybox.

Monitor Interface (BaseMonitor)
===============================

.. autoclass:: boofuzz.monitors.BaseMonitor
   :members:
   :undoc-members:
   :show-inheritance:

BusyboxMonitor
==============

.. autoclass:: boofuzz.monitors.BusyboxMonitor
   :members:
   :undoc-members:
   :show-inheritance:

.. important::

    The Target side of this monitor is available in the `monitors` directory at the root of the project, or just below :

    .. collapse:: Click Here

      .. literalinclude:: ../../monitors/busybox_monitor.sh
         :language: bash
         :linenos:

ProcessMonitor
==============

The process monitor consists of two parts; the ``ProcessMonitor`` class that implements
``BaseMonitor`` and a second module that is to be run on the host of your target.

.. autoclass:: boofuzz.monitors.ProcessMonitor
   :members:
   :undoc-members:

NetworkMonitor
==============

The network monitor consists of two parts; the ``NetworkMonitor`` class that implements
``BaseMonitor`` and a second module that is to be run on a host that can monitor the traffic.

.. autoclass:: boofuzz.monitors.NetworkMonitor
   :members:
   :undoc-members:

CallbackMonitor
===============

.. autoclass:: boofuzz.monitors.CallbackMonitor
   :members:
   :undoc-members:
