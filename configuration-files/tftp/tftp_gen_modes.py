#!/usr/bin/env python3
"""Simple TFTP demo for the final release, to test generation modes."""

from boofuzz import (
    Static,
    String,
    Bytes,
    Delim,
    Request,
    UDPSocketConnection,
    BaseConfig,
    TftpCallback,
    MultipleDefault)

class Config(BaseConfig):
    """Simple TFTP fuzzing session as a demo for different primitives and options.
    Sends just a few packets to test the generation modes."""
    host = "172.23.1.134"
    port = 69
    sleep_time = 0
    callback_module = TftpCallback
    socket = UDPSocketConnection
    recv_timeout = 0.1
    fuzz = True
    graph_filename = ""
    target_number = 2

    def config(self) -> None:
        """Configuration file for a TFTP fuzzing session"""

        wrq = Request("wrq", children=(
            Static(name="opcode", default_value="\x00\x02"),

            String(name="filename",
                   default_value="test",
                   seclist_path="home_made_seclists/seclist_test.txt",
                   use_long_strings=False,
                   use_default_value=False,
                   num_random_mutations=3,
                   num_random_generations=3,
                   max_rounds_mutation=1,
                   ),

            Delim(name="null",
                  default_value="\x00",
                  use_long_strings=False,
                  use_default_value=True,
                  num_random_mutations=1,
                  max_rounds_mutation=0,
                  num_random_generations=0,
                  min_len=2,
                  max_len=10,
                  padding="\x01"),

            MultipleDefault(name="mode", primitive=Static, values=["octet", "netascii"]),  # octet, netascii, mail

            Bytes(name="null2",
                  default_value=b'\0',
                  use_long_bytes=True,
                  num_library_elements=3,
                  use_default_value=False,
                  num_random_mutations=1,
                  max_rounds_mutation=0,
                  num_random_generations=0),
        ))

        self.session.connect(wrq)
