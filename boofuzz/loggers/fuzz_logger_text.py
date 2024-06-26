import sys

from colorama import init

from boofuzz import helpers

from boofuzz.loggers.ifuzz_logger_backend import IFuzzLoggerBackend

init()

DEFAULT_HEX_TO_STR = helpers.hex_to_hexstr


class FuzzLoggerText(IFuzzLoggerBackend):
    """
    This class formats FuzzLogger data for text presentation. It can be
    configured to output to STDOUT, or to a named file.

    Using two FuzzLoggerTexts, a FuzzLogger instance can be configured to output to
    both console and file.

    | Log level | Description                                                                    |
    | --------- | ------------------------------------------------------------------------------ |
    |     0     | Print on the same line the "open test case" log and also print fail, error     |
    |           | and target-error.                                                              |
    |     1     | Same as log level 0 but do not print on the same line.                         |
    |     2     | Log level 1 + check, pass, info and target-warn.                               |
    |     3     | Most verbose level : log level 2 + open test step, receive and send.           |
    """

    INDENT_SIZE = 2

    def __init__(self, file_handle=sys.stdout, bytes_to_str=DEFAULT_HEX_TO_STR, log_level: int = None):
        """
        :type file_handle: io.BinaryIO
        :param file_handle: Open file handle for logging. Defaults to sys.stdout.

        :type bytes_to_str: function
        :param bytes_to_str: Function that converts sent/received bytes data to string for logging.

        :type log_level: int
        :param log_level: Current log level. From 0 to 3. Default to 0.
        """
        self._file_handle = file_handle
        self._format_raw_bytes = bytes_to_str
        if log_level is not None:
            self.log_level = log_level
        else:
            if file_handle is sys.stdout:  # Default value if stdout
                self.log_level = 0
            else:  # Default value if not stdout
                self.log_level = 3

    def open_test_step(self, description):
        self._print_log_msg(msg=description, msg_type="step")

    def log_check(self, description):
        self._print_log_msg(msg=description, msg_type="check")

    def log_error(self, description):
        self._print_log_msg(msg=description, msg_type="error")

    def log_recv(self, data):
        self._print_log_msg(data=data, msg_type="receive")

    def log_send(self, data):
        self._print_log_msg(data=data, msg_type="send")

    def log_info(self, description):
        self._print_log_msg(msg=description, msg_type="info")

    def open_test_case(self, test_case_id, name, index, *args, **kwargs):
        self._print_log_msg(msg=test_case_id, msg_type="test_case")

    def log_fail(self, description=""):
        self._print_log_msg(msg=description, msg_type="fail")

    def log_target_warn(self, description=""):
        self._print_log_msg(msg=description, msg_type="target-warn")

    def log_target_error(self, description=""):
        self._print_log_msg(msg=description, msg_type="target-error")

    def log_pass(self, description=""):
        self._print_log_msg(msg=description, msg_type="pass")

    def log_recap(self, description=""):
        """Specific to FuzzLoggerText. Print a recap message."""
        self._print_log_msg(msg=description, msg_type="recap")

    def close_test_case(self):
        pass

    def close_test(self):
        pass

    def _print_final(self, msg_type, msg=None, data=None, begin='', end='\n'):
        print(
            begin +
            helpers.format_log_msg(msg_type=msg_type, description=msg, data=data, indent_size=self.INDENT_SIZE),
            file=self._file_handle, end=end
        )

    def _print_log_msg(self, msg_type, msg=None, data=None):
        level_1 = ['test_case', 'error', 'fail', 'recap', 'target-error']
        level_2 = level_1 + ['check', 'pass', 'info', 'target-warn']
        level_3 = level_2 + ['step', 'receive', 'send']

        unknow_msg_type = False
        if msg_type not in level_3:
            # Unknow msg_type.
            unknow_msg_type = True
            self.log_error(f'Unknow msg_type "{msg_type}" in FuzzLoggerText class')

        if self.log_level >= 3:
            self._print_final(msg_type, msg, data)
        elif self.log_level == 2 and (msg_type in level_2 or unknow_msg_type):
            self._print_final(msg_type, msg, data)
        elif self.log_level == 1 and (msg_type in level_1 or unknow_msg_type):
            self._print_final(msg_type, msg, data)
        elif self.log_level == 0 and (msg_type in level_1 or unknow_msg_type):
            if msg_type == 'test_case':
                self._print_final(msg_type, msg, data, begin='\r', end='\033[K')
            else:
                self._print_final(msg_type, msg, data, begin='\n', end='\n')
