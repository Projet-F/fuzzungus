import socket
import websocket

from boofuzz import exception
from boofuzz.connections import base_socket_connection, ip_constants

class WebSocketConnection(base_socket_connection.BaseSocketConnection):
    """BaseSocketConnection implementation for use with WebSocketConnection.

    .. versionadded:: 1.2.0

    Args:
        host (str): Hostname or IP adress of target system.
        port (int): Port of target service.
        uri (str): URI, example: "wss://example.com:12345" or "wss://$host+:+$port
        extra_headers {str:str}: extra headers which are used for connection
        subprotocols [str]: list of subprotocols accepted
        send_timeout (float): Seconds to wait for send before timing out. Default 5.0.
        recv_timeout (float): Seconds to wait for recv before timing out. Default 5.0.
        ping_interval (float): Seconds between ping_interval for the websocket. Default to 20.0
        max_size (int): max lenght of data in the websocket.
    """

    def __init__(self,host=None,port=None, uri=None, extra_headers={None:None},subprotocols=[],max_size=65536, send_timeout=5.0, recv_timeout=5.0, ping_interval=20.0,*args,**kwargs):
        super(WebSocketConnection, self).__init__(send_timeout, recv_timeout)

        self.uri = uri
        self.extra_headers = extra_headers
        self.subprotocols = subprotocols
        self.ping_interval=ping_interval
        self.max_size=max_size
        self.host = host
        self.port = port

        self.websocket=None

        if not(self.uri):
            if host and port:
                self.uri = "ws://" + host + ":" + str(port)
            else: 
                raise Exception("You have to define uri OR (host and port)")

    def open(self):
        self.websocket= websocket.create_connection(self.uri, extra_headers=self.extra_headers,
                                      subprotocols=self.subprotocols,ping_interval=self.ping_interval, max_size=self.max_size)

    def recv(self, max_bytes):

        self.websocket.settimeout(self._recv_timeout)
        data = b""

        try:
            data = self.websocket.recv()

        except socket.timeout as e:
            data = b""
            self.parent_target.parent_session.continue_case = False
            self.parent_target.get_fuzz_data_logger().log_error(f"{e} on recv(), RTO won't be computed.")
        
        return data.encode('utf-8')
    
    def send(self,data):
        """
        Send data to the target. Only valid after calling open!
        Some protocols will truncate; see self.max_size.

        Args:
            data: Data to send.

        Returns:
            int: Number of bytes actually sent.
        """
        data = data[: self.max_size]
        self.websocket.settimeout(self._send_timeout)

        try:
            self.websocket.send(data)

        except socket.timeout as e:
            self.parent_target.parent_session.continue_case = False
            self.parent_target.get_fuzz_data_logger().log_error(f"{e} on send(), RTO won't be computed.")

        return len(data)
    
    def close(self):
        self.websocket.close()
    
    @property
    def info(self):
        return "{0}:{1}".format(self.host, self.port)