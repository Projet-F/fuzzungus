#!/usr/bin/env python3
"""Demo websocket fuzzer."""

from boofuzz import Static, String, Bytes, Request, WebSocketConnection, BaseConfig, Group, WebsocketCallback



class Config(BaseConfig):
    """Class to define an Websocket fuzzing session"""
    uri = "ws://127.0.0.1:8765"
    sleep_time = 0
    callback_module = WebsocketCallback
    socket = WebSocketConnection
    target_number = 2

    def config(self) -> None:
        """Configuration file for a Websocket fuzzing session"""

        Data = Request("Data", children=(
            String(name="filename", default_value="Hello Word"),
        ))

        self.session.connect(Data)