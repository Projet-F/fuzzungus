#!/usr/bin/env python3
"""Demo TFTP fuzzer as a standalone script."""

from boofuzz import Static, String, Bytes, Request, Group, UDPSocketConnection, BaseConfig, TftpCallback, Session

def pre_send(self, target, fuzz_data_logger, session, *args, **kwargs):
    print("Appuyez sur entrée afin de continuer")
    input()

class Config(BaseConfig):
    """Class to define a simple TFTP fuzzing session with answer checking."""
    host = "172.23.1.134"
    port = 69
    sleep_time = 0
    pre_send = pre_send
    callback_module = TftpCallback
    socket = UDPSocketConnection
    recv_timeout = 2
    fuzz = True
    target_number = 2

    def config(self) -> None:
        """Configuration file for a TFTP fuzzing session"""

        RRQ = Request("RRQ", children=(
                        Static(name="opcode", default_value=b'\x00\x01'),
                        Group(name="filename", values=["toto.txt","toto.txt","test.txt"]),
                        Static(name="null", default_value=b'\0'),
                        Group(name="mode", values=["octet","netasciiiiii"]),
                        Static(name="null2", default_value=b'\0'),
                    ),
                answer_must_contain=["test de la recette"],
                answer_must_not_contain=["File not found"]
        )

        self.session.connect(RRQ)