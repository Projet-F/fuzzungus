"""Base class for every configuration file"""

import os
import typing

from boofuzz.connections import BaseSocketConnection, UDPSocketConnection
from boofuzz.callbacks.base_callback import BaseCallback
from boofuzz.monitors import BaseMonitor
from .session import Session
from .target import Target


class BaseConfig:
    """
    Base class for every configuration file.
    Below are the attributes of the general configuration : 

    :type host: str
    :param host: Host to connect to
    :type port: int
    :param port: Port to connect to
    :type callback_module: BaseCallback
    :param callback_module: Callback module to use
    :type socket: BaseSocketConnection
    :param socket: Socket connection to use
    :type recv_timeout: float
    :param recv_timeout: Time to wait for a response
    :type fuzz: bool
    :param fuzz: Enable fuzzing
    :type target_number: int
    :param target_number: Number of targets to add
    :external_monitor: BaseMonitor()
    :param external_monitor: External monitor to use. Should be instantiated in the configuration file.
    :type meth_for_monitor_alive: list[typing.Callable]
    :param meth_for_monitor_alive: List of methods to call for when the target is alive
    :type pre_send: typing.Callable
    :param pre_send: Pre send callback
    :type post_test_case: typing.Callable
    :param post_test_case: Post test case callback

    And here every :class:`Session` attributes:

    .. autoclass:: Session
        :no-index:

    .. note::
        Not every :class:`Session` attributes are hard-wired as parameters of this class below.
        We thougth of using a dictionnary to reproduce the behavior of `*args` and `**kwargs` in `__init__` methods.
        But we decided to restrain the number of parameters to avoid confusion.
        So if you need a :class:`Session` attribute that is not in the list below, you should edit this file and add it below.
    """

    # Network
    host: str = ""
    port: int = 0
    uri: str = ""
    socket: BaseSocketConnection = UDPSocketConnection
    target_number: int = 1
    recv_timeout: float = 10

    # Campaign
    fuzz: bool = True
    round_type: str = "library"
    sleep_time: float = 0
    nominal_test_interval: int = 50
    restart_sleep_time: float = 1
    receive_data_after_each_request: bool = True
    receive_data_after_fuzz: bool = True
    max_depth: int = 1

    # Callback
    callback_module: BaseCallback = BaseCallback
    pre_send: typing.Callable = None
    post_test_case: typing.Callable = None

    # Monitor
    external_monitor: BaseMonitor|None = None
    meth_for_monitor_alive: list[typing.Callable]|None = None

    def __init__(
            self,
            campaign_folder: str = None,
            log_level_stdout: int = 0,
            db_name: str = None,
            db_table_name: str | None = None
    ):
        # Attributes
        self.log_level_stdout = log_level_stdout
        self.campaign_folder = campaign_folder
        self.db_name = db_name
        self.db_table_name = db_table_name
        self.session: Session | None = None
        self.cb = self.callback_module()

        if self.pre_send is None:
            self.pre_send = self.cb.pre_send

        if self.post_test_case is None:
            self.post_test_case = self.cb.post_test_case

    def session_init(self) -> None:
        """Initialize the session with the target and the callbacks"""
        self.session = Session(
            target=Target(
                connection=self.socket(
                    host = self.host,
                    port = self.port,
                    uri = self.uri,
                    recv_timeout=self.recv_timeout),
                monitors=self.external_monitor,
                monitor_alive=self.meth_for_monitor_alive
            ),
            receive_data_after_each_request=self.receive_data_after_each_request,
            receive_data_after_fuzz=self.receive_data_after_fuzz,
            pre_send_callbacks=[self.pre_send],
            post_test_case_callbacks=[self.post_test_case],
            sleep_time=self.sleep_time,
            log_level_stdout=self.log_level_stdout,
            db_name=self.db_name,
            db_table_name=self.db_table_name,
            restart_sleep_time=self.restart_sleep_time,
            round_type=self.round_type,
            nominal_test_interval=self.nominal_test_interval,
            campaign_folder=self.campaign_folder
        )

        # For loop to add multiple targets
        for _ in range(self.target_number - 1):  # The first target is already created in the initialisation
            self.session.add_target(Target(
                connection=self.socket(
                    host = self.host,
                    port = self.port,
                    uri = self.uri,
                    recv_timeout=self.recv_timeout)
            ))

    def graph_generation(self, graph_name) -> None:
        """Generate the graph of the session"""
        with open(graph_name, 'wb') as file:
            file.write(self.session.render_graph_graphviz().create_png())  # pylint: disable=no-member

    def config(self) -> None:
        """Configuration file for every session"""
        raise NotImplementedError("config method not implemented")

    def config_nominal(self) -> None:
        """Configuration of nominal data for test"""
        return  # Nominal test is optional so don't raise a NotImplementedError

    @staticmethod
    def nominal_recv_test(session: Session) -> bool:
        return True  # Nominal recv test is optional. Default to True
