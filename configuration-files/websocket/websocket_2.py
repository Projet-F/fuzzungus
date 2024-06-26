#!/usr/bin/env python3
"""Demo websocket fuzzer."""

from boofuzz import Static, String, Bytes, Request, WebSocketConnection, BaseConfig, Group, WebsocketCallback

def pre_send(self, target, fuzz_data_logger, session, *args, **kwargs):
    print("Appuyez sur entrée afin de continuer")
    input()

class Config(BaseConfig):
    """Class to define an Websocket fuzzing session"""
    uri = "ws://127.0.0.1:8765"
    sleep_time = 0
    callback_module = WebsocketCallback
    socket = WebSocketConnection
    target_number = 2
    pre_send = pre_send

    def config(self) -> None:
        """Configuration file for a Websocket fuzzing session"""

        data = Request("Data", children=(
            String(name="filename",
                default_value="test",
                seclist_path="home_made_seclists/seclist_test.txt",
                use_long_strings=False,
                use_default_value=False,
                num_random_mutations=0,
                num_random_generations=0,
                max_rounds_mutation=0,
                ),
        ))

        self.session.connect(data)

