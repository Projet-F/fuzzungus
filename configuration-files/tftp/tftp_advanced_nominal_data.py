#!/usr/bin/env python3
"""Advanced TFTP fuzzing session"""

from boofuzz import Static, String, Bytes, MultipleDefault, Request, UDPSocketConnection, BaseConfig, TftpCallback, \
    Session


class Config(BaseConfig):
    """Class to define an advanced TFTP fuzzing session, with nominal data example."""
    host = "172.23.1.134"
    port = 69
    sleep_time = 0
    callback_module = TftpCallback
    socket = UDPSocketConnection
    recv_timeout = 2
    fuzz = True
    target_number = 2

    # See https://datatracker.ietf.org/doc/html/rfc1350
    def config(self) -> None:
        """Configuration file for a TFTP fuzzing session"""

        rrq = Request("rrq", children=(
            Static(name="opcode", default_value="\x00\x01"),
            String(name="filename", default_value="test"),
            Bytes(name="null", default_value=b'\0'),
            MultipleDefault(name="mode", values=["octet", "netascii"], fuzzable=False, max_len=32, primitive=String),
            Bytes(name="null2", default_value=b'\0'),
        ))

        wrq = Request("wrq",
                      timeout_check=False,
                      children=(
                          Static(name="opcode", default_value="\x00\x02"),
                          String(name="filename", default_value="test"),
                          Bytes(name="null", default_value=b'\0'),
                          MultipleDefault(name="mode", values=["octet", "netascii"], primitive=String),
                          Bytes(name="null2", default_value=b'\0'),
                      )
                      )

        data = Request("data",
                       timeout_check=False,
                       children=(
                           Static(name="opcode", default_value="\x00\x03"),
                           Static(name="block", default_value="\x00\x01"),
                           Bytes(name="data", default_value=b'\0'),
                       )
                       )

        ack = Request("ack", children=(
            Static(name="opcode", default_value="\x00\x04"),
            Bytes(name="block", default_value=b'\0\0'),
        ))

        error = Request("error", children=(
            Static(name="opcode", default_value="\x00\x05"),
            Bytes(name="error_code", default_value=b"\1"),
            String(name="error_msg", default_value="File not found"),
            Bytes(name="null", default_value=b'\0'),
        ))

        self.session.connect(wrq)
        self.session.connect(rrq)
        self.session.connect(wrq, data, callback=self.cb.control_to_data)
        self.session.connect(rrq, ack, callback=self.cb.control_to_data)
        self.session.connect(wrq, error, callback=self.cb.control_to_data)
        self.session.connect(rrq, error, callback=self.cb.control_to_data)

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
