from boofuzz.callbacks.base_callback import BaseCallback


class WebsocketCallback(BaseCallback):
    """ Callback class for Web socket protocol """

    def __init__(self):
        super().__init__()

    def pre_send(self, target, fuzz_data_logger, session, *args, **kwargs):
        """
            This is the post send function for Websocket, clear all current connection.
            Close all targets, use the default port, use first target and open it
        """

    def post_test_case(self, target, fuzz_data_logger, session, *args, **kwargs):
        ...