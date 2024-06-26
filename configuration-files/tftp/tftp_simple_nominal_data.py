#!/usr/bin/env python3
"""Demo TFTP fuzzer as a standalone script."""

from boofuzz import Static, String, Bytes, Request, UDPSocketConnection, BaseConfig, TftpCallback, Session


class Config(BaseConfig):
    """Class to define a simple TFTP fuzzing session, wiht nominal data check."""
    host = "172.23.1.134"
    port = 69
    sleep_time = 0
    callback_module = TftpCallback
    socket = UDPSocketConnection
    recv_timeout = 2
    fuzz = True
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
                   num_random_mutations=10,
                   num_random_generations=10,
                   max_rounds_mutation=1),

            Bytes(name="null",
                  default_value=b'\0',
                  num_library_elements=2,
                  num_random_mutations=3,
                  num_random_generations=5, ),

            Static(name="mode", default_value="octet"),  # octet, netascii, mail

            Bytes(name="null2",
                  default_value=b'\0',
                  num_library_elements=1,
                  num_random_mutations=1,
                  num_random_generations=1,
                  max_rounds_mutation=1),
        ),answer_must_contain=[b'\x00\x04\x00\x00'],answer_must_not_contain=["File not found"])

        data = Request("data", children=(
            Static(name="opcode", default_value="\x00\x03"),
            Static(name="block", default_value="\x00\x01"),
            Bytes(name="data",
                  default_value=b'\0',
                  num_library_elements=1,
                  num_random_mutations=1,
                  num_random_generations=5,
                  max_rounds_mutation=1,
                  min_len=15000,
                  max_len=20000),
        ))

        self.session.connect(wrq)
        self.session.connect(wrq, data, callback=self.cb.control_to_data)

    def config_nominal(self) -> None:
        rrq = Request("rrq", children=(
            Static(name="opcode", default_value="\x00\x01"),
            Static(name="filename", default_value="nominal_test"),
            Static(name="null", default_value=b'\0'),
            Static(name="mode", default_value="octet"),
            Static(name="null2", default_value=b'\0'),
        ))

        self.session.set_nominal_data([rrq])

    @staticmethod
    def nominal_recv_test(session: Session) -> bool:
        expected_data = b'\x00\x03\x00\x01nominal_data\n'
        test = session.last_recv == expected_data
        if not test:
            session.get_fuzz_data_logger().log_info(f'Error in recv data (nominal test). The recv data should have been'
                                                    f'"{expected_data}"')
        return test
