import abc
import math
import os
import socket
import struct

from . import itarget_connection


def _seconds_to_sockopt_format(seconds):
    """Convert floating point seconds value to second/useconds struct used by UNIX socket library.
    For Windows, convert to whole milliseconds.
    """
    if os.name == "nt":
        return int(seconds * 1000)
    else:
        microseconds_per_second = 1000000
        whole_seconds = int(math.floor(seconds))
        whole_microseconds = int(math.floor((seconds % 1) * microseconds_per_second))
        return struct.pack("ll", whole_seconds, whole_microseconds)


class BaseSocketConnection(itarget_connection.ITargetConnection, metaclass=abc.ABCMeta):
    """This class serves as a base for a number of Connections over sockets.

    .. versionadded:: 0.2.0

    Args:
        send_timeout (float): Sets the timeout value specifying the amount of time that an output
            function blocks because flow control prevents data from being sent. 
            Default 0 : The recv_timeout is used for all operations.
        recv_timeout (float): Sets the timeout value that specifies the maximum amount of time an 
            input function waits until it completes. Default 5.0.
    """

    def __init__(self, send_timeout, recv_timeout):
        # Not a really clean solution, but allows to type parent_target without circular import
        from ..sessions import target

        # Set default timeout for all new sockets
        # This prevents new sockets to be created in blocking mode
        socket.setdefaulttimeout(recv_timeout)

        # Parameters
        self._send_timeout = send_timeout
        self._recv_timeout = recv_timeout
        # TODO : Solve circular import when typing parent_target
        self.parent_target:target.Target = None
        self._sock: socket.socket|None = None

    def close(self):
        """
        Close connection to the target.

        Returns:
            None
        """
        self._sock.close()

    @abc.abstractmethod
    def open(self):
        """
        Opens connection to the target. Make sure to call close!

        Returns:
            None
        """
        self._sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_SNDTIMEO,
                _seconds_to_sockopt_format(self._send_timeout))
        self._sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_RCVTIMEO,
            _seconds_to_sockopt_format(self._recv_timeout))

    def get_recv_timeout(self):
        """
        Get the current recv timeout.

        Returns:
            float: The current recv timeout.
        """
        return self._recv_timeout

    def get_send_timeout(self):
        """
        Get the current send timeout.

        Returns:
            float: The current send timeout.
        """
        return self._send_timeout
