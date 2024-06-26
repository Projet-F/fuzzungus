"""Module for the Target class."""
import time
import warnings
import typing

from boofuzz.connections import ITargetConnection
from boofuzz.monitors import BaseMonitor
from boofuzz.monitors import pedrpc
from boofuzz.loggers import IFuzzLogger


class Target:
    """
    Target descriptor container.

    Takes an ITargetConnection and wraps send/recv with appropriate FuzzDataLogger calls.

    Encapsulates pedrpc connection logic.

    Contains a logger which is configured by :meth:`Session.add_target()`.

    Example:

    .. code-block:: python

        tcp_target = Target(SocketConnection(host='127.0.0.1', port=17971))


    :param connection: Connection to system under test.
    :type connection: ITargetConnection
    :param monitors: List of Monitors for this Target.
    :type monitors: list[BaseMonitor, pedrpc.Client]|BaseMonitor|pedrpc.Client
    :param monitor_alive: List of Functions that are called when a Monitor is alive. 
        It is passed the monitor instance that became alive. Use it to e.g. set options on restart.
        The methods passed here should accept the following arguments:
        - monitor (self): The monitor that became alive.
        - fuzz_data_logger: The fuzz data logger.
        - parent_session: The parent session.
        Otherwise, use \*args and \*\*kwargs to accept any arguments.
    :type monitor_alive: typing.Callable
    :param max_recv_bytes: Maximum number of bytes to receive. Default 10000.
    :type max_recv_bytes: int
    :param repeater: Repeater to use for sending. Default None.
    :type repeater: repeater.Repeater
    :param procmon: Deprecated interface for adding a process monitor.
    :type procmon: BaseMonitor
    :param procmon_options: Deprecated interface for adding a process monitor.
    :type procmon_options: dict       

    .. versionchanged:: 0.4.2
       This class has been moved into the sessions subpackage. The full path is now boofuzz.sessions.target.Target.
    """

    def __init__(
        self,
        connection,
        monitors:list[BaseMonitor, pedrpc.Client]|BaseMonitor|pedrpc.Client|None=None,
        monitor_alive:typing.Callable=None,
        max_recv_bytes=10000,
        repeater=None,
        procmon=None,
        procmon_options=None,
        **kwargs
    ):
        self._fuzz_data_logger:IFuzzLogger = None
        self.parent_session = None
        self._target_connection = connection
        self.max_recv_bytes = max_recv_bytes
        self.repeater = repeater
        # If the monitor is a lone monitor, wrap it in a list.
        if isinstance(monitors, BaseMonitor):
            monitors = [monitors]
        # If the monitor is None, set it to an empty list.
        self.monitors:list[BaseMonitor] = monitors if monitors is not None else []
        if procmon is not None:
            if procmon_options is not None:
                procmon.set_options(**procmon_options)
            self.monitors.append(procmon)

        self.monitor_alive = monitor_alive if monitor_alive is not None else []

        if "procmon" in kwargs.keys() and kwargs["procmon"] is not None:
            warnings.warn(
                "Target(procmon=...) is deprecated. Please change your code"
                " and add it to the monitors argument. For now, we do this "
                "for you, but this will be removed in the future.",
                FutureWarning,
            )
            self.monitors.append(kwargs["procmon"])

        if "netmon" in kwargs.keys() and kwargs["netmon"] is not None:
            warnings.warn(
                "Target(netmon=...) is deprecated. Please change your code"
                " and add it to the monitors argument. For now, we do this "
                "for you, but this will be removed in the future.",
                FutureWarning,
            )
            self.monitors.append(kwargs["netmon"])

        # set these manually once target is instantiated.
        self.vmcontrol = None
        self.vmcontrol_options = {}

    @property
    def netmon_options(self):
        raise NotImplementedError(
            "This property is not supported; grab netmon from monitors and use set_options(**dict)"
        )

    @property
    def procmon_options(self):
        raise NotImplementedError(
            "This property is not supported; grab procmon from monitors and use set_options(**dict)"
        )

    def get_connection(self) -> ITargetConnection :
        """
        Get the connection object.

        :return: Connection object.
        """
        return self._target_connection

    def close(self):
        """
        Close connection to the target.

        :return: None
        """
        self._fuzz_data_logger.log_info("Closing target connection...")
        self._target_connection.close()
        self._fuzz_data_logger.log_info("Connection closed.")

    def open(self):
        """
        Opens connection to the target. Make sure to call close!

        :return: None
        """
        self._fuzz_data_logger.log_info("Opening target connection ({0})...".format(self._target_connection.info))
        self._target_connection.open()
        self._fuzz_data_logger.log_info("Connection opened.")

    def pedrpc_connect(self):
        warnings.warn(
            "pedrpc_connect has been renamed to monitors_alive. "
            "This alias will stop working in a future version of boofuzz.",
            FutureWarning,
        )

        return self.monitors_alive()

    def monitors_alive(self):
        """
        Wait for the monitors to become alive / establish connection to the RPC server.
        This method is called on every restart of the target and when it's added to a session.
        After successful probing, a callback is called, passing the monitor.

        :return: None
        """

        for monitor in self.monitors:
            self._fuzz_data_logger.log_info("Waiting for monitors to become alive...")
            while True:
                if monitor.alive(fuzz_data_logger=self._fuzz_data_logger):
                    break
                time.sleep(1)
            if self.monitor_alive:
                for monitor_method_if_alive in self.monitor_alive:
                    # If the method is a function of the monitor class, call it.

                    if self._check_if_method_belongs_to_monitor(monitor, monitor_method_if_alive):
                        monitor_method_if_alive(monitor, fuzz_data_logger=self._fuzz_data_logger, session=self.parent_session)

    def recv(self, max_bytes=None):
        """
        Receive up to max_bytes data from the target.

        Args:
            max_bytes (int): Maximum number of bytes to receive.

        Returns:
            Received data.
        """
        if max_bytes is None:
            max_bytes = self.max_recv_bytes

        if self._fuzz_data_logger is not None:
            self._fuzz_data_logger.log_info("Receiving...")

        data = self._target_connection.recv(max_bytes=max_bytes)

        if self._fuzz_data_logger is not None:
            self._fuzz_data_logger.log_recv(data)

        return data

    def send(self, data):
        """
        Send data to the target. Only valid after calling open!

        Args:
            data: Data to send.

        Returns:
            None
        """
        num_sent = 0
        if self._fuzz_data_logger is not None:
            repeat = ""
            if self.repeater is not None:
                repeat = ", " + self.repeater.log_message()

            self._fuzz_data_logger.log_info("Sending {0} bytes{1}...".format(len(data), repeat))

        if self.repeater is not None:
            self.repeater.start()
            while self.repeater.repeat():
                num_sent = self._target_connection.send(data=data)
            self.repeater.reset()
        else:
            num_sent = self._target_connection.send(data=data)

        if self._fuzz_data_logger is not None:
            self._fuzz_data_logger.log_send(data[:num_sent])

    def set_fuzz_data_logger(self, fuzz_data_logger):
        """
        Set this object's fuzz data logger -- for sent and received fuzz data.

        :param fuzz_data_logger: New logger.
        :type fuzz_data_logger: ifuzz_logger.IFuzzLogger

        :return: None
        """
        self._fuzz_data_logger = fuzz_data_logger

    def get_fuzz_data_logger(self):
        """
        Get this object's fuzz data logger -- for sent and received fuzz data.

        :return: IFuzzLogger
        """
        return self._fuzz_data_logger

    def _check_if_method_belongs_to_monitor(self, monitor, method):
        """
        Check if a method belongs to a monitor, by comparing the method's qualname to the monitor's method qualname.
        
        return: bool
        """

        try:
            # First, get the qualified name of the method, like "BusyboxMonitor.post_send"
            method_qualname = method.__qualname__

            # Then, get the method name, like "post_send"
            method_name = method.__name__

            # Then, get the monitor class, like "<class 'boofuzz.monitors.busybox_monitor.BusyboxMonitor'>"
            monitor_class_name = monitor.__class__

            # Then, get the method from the monitor class, like "<function BusyboxMonitor.post_send at 0x7f70e1368f40>"
            monitor_method_name = getattr(monitor_class_name, method_name)

            # Then, get the monitor method qualname, like ""
            monitor_method_qualname = monitor_method_name.__qualname__

            # Finally, compare the method qualname to the monitor method qualname
            if method_qualname == monitor_method_qualname:
                return True

            return False

        except Exception :
            return False