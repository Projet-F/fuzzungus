"""Callback functions for every protocol"""


class BaseCallback:
    """Base Callback class"""

    def __init__(self):
        pass

    def post_test_case(self, target, fuzz_data_logger, session, *args, **kwargs):
        """ Function which is used in post send (after the fuzzed node) """

        raise NotImplementedError("This function should be implemented in the child class")

    def pre_send(self, target, fuzz_data_logger, session, *args, **kwargs):
        """
            This is the post send function for TFTP, clear all current connection.
            Close all targets, use the default port, use first target and open it
        """
        raise NotImplementedError("This function should be implemented in the child class")

