"""Callback functions for the TFTP protocol"""

import time
from boofuzz.callbacks.base_callback import BaseCallback


class TftpCallback(BaseCallback):
    """ Callback class for TFTP protocol """

    host = "0.0.0.0"
    port_to_listen = 69

    def __init__(self):
        super().__init__()

    def control_to_data(self, target, fuzz_data_logger, session, *args, **kwargs):
        """
            This function is used to change our target from the control port (69 by default in TFTP)
            to the data port (the one that target use to reply)
        """
        session.targets[
            session.target_to_use].close()  # When we got an answer, we now know which port to use so we close the default one
        session.target_to_use = 1  # We swap to the second port
        session.targets[session.target_to_use].get_connection().use_same_port(session.targets[0].get_connection())
        if session.targets[0].get_connection().get_udp_client_port()[1] == self.port_to_listen:
            fuzz_data_logger.log_error("Wrong port")
        session.targets[session.target_to_use].get_connection().port = \
            session.targets[0].get_connection().get_udp_client_port()[1]  # we set the new port
        session.targets[session.target_to_use].open()  # we open connection

    def post_test_case(self, target, fuzz_data_logger, session, *args, **kwargs):
        """ Function which is used in post send (after the fuzzed node) """
        if session.fuzz_node.name == "data":
            pass
        if "wrq" in session.fuzz_node.name:
            pass
        if "rrq" in session.fuzz_node.name:
            self.send_ack_after_data(target=target, fuzz_data_logger=fuzz_data_logger, session=session)

        if session.last_send is not None:
            for target in session.targets:
                if target.get_connection().get_sock() is not None:
                    target.close()
                target.get_connection().bind = None
            session.target_to_use = 0

    def pre_send(self, target, fuzz_data_logger, session, *args, **kwargs):
        """
            This is the post send function for TFTP, clear all current connection.
            Close all targets, use the default port, use first target and open it
        """

    def send_ack_after_data(self, target, fuzz_data_logger, session, *args, **kwargs):
        """Function used in case we don't fuzze the ack node and we would like to reply normally for each Data packet
        """

        self.control_to_data(target=target, fuzz_data_logger=fuzz_data_logger, session=session, node=None, edge=None,
                             test_case_context=None)
        while (
                len(session.last_recv) == 516):  # While it's not the last packet, get the num block and send an ack with it
            data = b"\x00\x04" + self.get_num_block(session=session)
            session.targets[session.target_to_use].send(data)
            session.last_recv = session.targets[session.target_to_use].recv()
        data = b"\x00\x04" + self.get_num_block(session=session)
        session.targets[session.target_to_use].send(data)

    def get_num_block(self, session):
        """ Return the num block in a data packet or ack packet """

        return (session.last_recv[2] * 256 + session.last_recv[3]).to_bytes(2, byteorder='big')

    def fragmentation(self, session, sock, node, edge, callback_data, mutation_context, length):
        null = 0
        index_byte = 0
        if node == session.fuzz_node:
            data = session.fuzz_node.render(mutation_context)
        else:
            data = node.render(mutation_context=mutation_context)
        while len(data) - index_byte > length + 4:
            data_to_send = data[0:4] + data[4 + index_byte:length + 4 + index_byte]
            yield data_to_send
            index_byte += length
            if data[3] == 0xFF:
                data = data[0:2] + (data[2] + 1).to_bytes(1, byteorder='big') + data[3:]
                data = data[0:3] + null.to_bytes(1, byteorder='big') + data[4:]
            else:
                data = data[0:3] + (data[3] + 1).to_bytes(1, byteorder='big') + data[4:]
        data_to_send = data[0:4] + data[4 + index_byte:]
        yield data_to_send
