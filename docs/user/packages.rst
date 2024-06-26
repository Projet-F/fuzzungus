.. _packages :

Packages
========

The whole Boofuzz project package diagram looks something like this :

.. digraph:: boofuzz_project

    node[
        shape=record
        style=filled
		fillcolor=gray95
    ]
    size=10

    boofuzz -> {blocks callbacks cli connections ip_constants constants event_hook exception fuzzable fuzable_block loggers monitors pedrpc primitives protocol_session protocol_session_reference repeater sessions process_monitor_local};
    blocks -> {aligned block checksum repeat request size};
    request -> primitives;
    callbacks -> {base_callback tftp_callback};
    tftp_callback -> base_callback;

    cli -> {cli_context connections constants helpers fuzz_logger_csv fuzz_logger_curses fuzz_logger_text monitors debugger_thread_simple process_monitor_local};
    cli_context -> sessions
    connections -> base_socket_connection
    connections -> file_connection
    connections -> iserial_like
    connections -> itarget_connection
    connections -> netconf_connection
    connections -> raw_l2_socket_connection
    connections -> raw_l3_socket_connection
    connections -> serial_connection
    connections -> serial_connection_low_level
    connections -> socket_connection
    connections -> ssl_socket_connection
    connections -> tcp_socket_connection
    connections -> udp_socket_connection
    connections -> unix_socket_connection
    base_socket_connection -> connections
    base_socket_connection -> itarget_connection
    netconf_connection -> connections
    netconf_connection -> itarget_connection
    raw_l2_socket_connection -> boofuzz
    raw_l2_socket_connection -> connections
    raw_l2_socket_connection -> base_socket_connection
    raw_l2_socket_connection -> exception
    raw_l3_socket_connection -> boofuzz
    raw_l3_socket_connection -> connections
    raw_l3_socket_connection -> base_socket_connection
    raw_l3_socket_connection -> exception
    serial_connection -> connections
    serial_connection -> itarget_connection
    serial_connection -> serial_connection_low_level
    serial_connection_low_level -> connections
    serial_connection_low_level -> iserial_like
    socket_connection -> boofuzz
    socket_connection -> connections
    socket_connection -> raw_l2_socket_connection
    socket_connection -> raw_l3_socket_connection
    socket_connection -> ssl_socket_connection
    socket_connection -> tcp_socket_connection
    socket_connection -> udp_socket_connection
    socket_connection -> exception
    ssl_socket_connection -> boofuzz
    ssl_socket_connection -> connections
    ssl_socket_connection -> tcp_socket_connection
    ssl_socket_connection -> exception
    tcp_socket_connection -> boofuzz
    tcp_socket_connection -> connections
    tcp_socket_connection -> base_socket_connection
    tcp_socket_connection -> exception
    udp_socket_connection -> boofuzz
    udp_socket_connection -> connections
    udp_socket_connection -> base_socket_connection
    udp_socket_connection -> ip_constants
    udp_socket_connection -> exception
    unix_socket_connection -> boofuzz
    unix_socket_connection -> connections
    unix_socket_connection -> base_socket_connection
    unix_socket_connection -> exception
    fuzzable -> mutation
    fuzzable -> mutation_context
    fuzzable -> protocol_session_reference
    fuzzable_block -> fuzzable
    fuzzers -> exception
    helpers -> connections
    helpers -> ip_constants
    helpers -> udp_socket_connection
    helpers -> exception
    loggers -> fuzz_logger
    loggers -> fuzz_logger_csv
    loggers -> fuzz_logger_curses
    loggers -> fuzz_logger_db
    loggers -> fuzz_logger_text
    loggers -> ifuzz_logger
    loggers -> ifuzz_logger_backend
    fuzz_logger -> ifuzz_logger
    fuzz_logger_csv -> boofuzz
    fuzz_logger_csv -> helpers
    fuzz_logger_csv -> ifuzz_logger_backend
    fuzz_logger_curses -> boofuzz
    fuzz_logger_curses -> helpers
    fuzz_logger_curses -> ifuzz_logger_backend
    fuzz_logger_db -> boofuzz
    fuzz_logger_db -> data_test_case
    fuzz_logger_db -> data_test_step
    fuzz_logger_db -> exception
    fuzz_logger_db -> helpers
    fuzz_logger_db -> ifuzz_logger_backend
    fuzz_logger_text -> boofuzz
    fuzz_logger_text -> helpers
    fuzz_logger_text -> ifuzz_logger_backend
    ifuzz_logger_backend -> ifuzz_logger
    main -> boofuzz
    monitors -> base_monitor
    monitors -> callback_monitor
    monitors -> network_monitor
    monitors -> process_monitor
    callback_monitor -> boofuzz
    callback_monitor -> constants
    callback_monitor -> exception
    callback_monitor -> base_monitor
    external_monitor -> base_monitor
    network_monitor -> base_monitor
    pedrpc -> boofuzz
    pedrpc -> exception
    process_monitor -> base_monitor
    mutation_context -> protocol_session
    pgraph -> cluster

    E [label="edge"];
    G [label="graph"];
    N [label="node"];
    pgraph -> E
    pgraph -> G
    pgraph -> N
    primitives -> base_primitive
    primitives -> bit_field
    primitives -> byte
    primitives -> bytes
    primitives -> delim
    primitives -> dword
    primitives -> float
    primitives -> from_file
    primitives -> group
    primitives -> mirror
    primitives -> multipledefault
    primitives -> qword
    primitives -> random_data
    primitives -> simple
    primitives -> static
    primitives -> string
    primitives -> word
    bit_field -> base_primitive
    byte -> bit_field
    bytes -> base_primitive
    delim -> string
    dword -> bit_field
    float -> base_primitive
    from_file -> base_primitive
    group -> base_primitive
    mirror -> base_primitive
    multipledefault -> base_primitive
    qword -> bit_field
    random_data -> boofuzz
    random_data -> helpers
    random_data -> base_primitive
    simple -> base_primitive
    static -> base_primitive
    string -> base_primitive
    word -> bit_field
    sessions -> base_config
    sessions -> connection
    sessions -> session
    sessions -> session_info
    sessions -> target
    sessions -> web_app
    base_config -> callbacks
    base_config -> connections
    base_config -> session
    base_config -> target
    session -> boofuzz
    session -> blocks
    session -> constants
    session -> event_hook
    session -> exception
    session -> helpers
    session -> loggers
    session -> fuzz_logger
    session -> fuzz_logger_curses
    session -> fuzz_logger_db
    session -> fuzz_logger_text
    session -> monitors
    session -> mutation_context
    session -> pgraph
    session -> primitives
    session -> static
    session -> protocol_session
    session -> connection
    session -> session_info
    session -> target
    session -> web_app
    session -> app
    target -> connections
    web_app -> boofuzz
    web_app -> constants
    web_app -> app
    process_monitor_local -> boofuzz
    process_monitor_local -> base_monitor
    process_monitor_local -> utils
    process_monitor_pedrpc_server -> boofuzz
    process_monitor_pedrpc_server -> utils
    request -> sessions [label=dependency]
    fuzzable -> request [label=dependency]

To make it all a little bit more understandable, we decided to devide it into section, the main one being the top package Boofuzz, described below. 
You can go in the corresponding package section below to see the contained classes. 

We decided to generate a package diagram instead of a class diagram because :

- The goal of this page is not to show the attributes and methods of each class, as this is already shown in the API documentation, but to show the relationships between the classes.
- The class diagram would be too big and unreadable



This was generated using the `Pyverse <https://pylint.readthedocs.io/en/latest/pyreverse.html>`_ tool from the `Pylint <https://pylint.readthedocs.io/en/latest/index.html>`_ package. 
Those diagrams do not represent every relations in the project, as we manually removed some of them to make it more readable. And so will not be updated automatically.

Boofuzz
-------

.. digraph:: boofuzz

    node[
        shape=record
        style=filled
		fillcolor=gray95
    ]
    size=10

    rankdir=LR;

    boofuzz -> blocks
    boofuzz -> callbacks
    boofuzz -> cli
    boofuzz -> connections
    boofuzz -> ip_constants
    boofuzz -> constants
    boofuzz -> event_hook
    boofuzz -> exception
    boofuzz -> fuzzable
    boofuzz -> fuzzable_block
    boofuzz -> loggers
    boofuzz -> monitors
    boofuzz -> pedrpc
    boofuzz -> primitives
    boofuzz -> protocol_session
    boofuzz -> protocol_session_reference
    boofuzz -> repeater
    boofuzz -> sessions
    boofuzz -> process_monitor_local


Blocks
------

.. digraph:: boofuzz

    node[
        shape=record
        style=filled
		fillcolor=gray95
    ]
    size=10
    rankdir=LR;

    blocks -> aligned
    blocks -> block
    blocks -> checksum
    blocks -> repeat
    blocks -> request
    blocks -> size

Callbacks
---------

.. digraph:: boofuzz

    node[
        shape=record
        style=filled
		fillcolor=gray95
    ]
    size=10
    rankdir=LR;

    callbacks -> base_callback
    callbacks -> tftp_callback
    tftp_callback -> base_callback

CLI
---

.. digraph:: boofuzz

    node[
        shape=record
        style=filled
		fillcolor=gray95
    ]
    size=10
    rankdir=LR;

    cli -> cli_context
    cli_context -> sessions
    cli -> connections
    cli -> constants
    cli -> helpers
    cli -> fuzz_logger_csv
    cli -> fuzz_logger_curses
    cli -> fuzz_logger_text
    cli -> monitors
    cli -> debugger_thread_simple
    cli -> process_monitor_local

Connections
-----------

.. digraph:: boofuzz

    node[
        shape=record
        style=filled
		fillcolor=gray95
    ]
    size=10
    rankdir=LR;

    connections -> base_socket_connection
    connections -> file_connection
    connections -> iserial_like
    connections -> itarget_connection
    connections -> netconf_connection
    connections -> raw_l2_socket_connection
    connections -> raw_l3_socket_connection
    connections -> serial_connection
    connections -> serial_connection_low_level
    connections -> socket_connection
    connections -> ssl_socket_connection
    connections -> tcp_socket_connection
    connections -> udp_socket_connection
    connections -> unix_socket_connection
    base_socket_connection -> connections
    base_socket_connection -> itarget_connection
    netconf_connection -> connections
    netconf_connection -> itarget_connection
    raw_l2_socket_connection -> connections
    raw_l2_socket_connection -> base_socket_connection
    raw_l3_socket_connection -> connections
    raw_l3_socket_connection -> base_socket_connection
    serial_connection -> connections
    serial_connection -> itarget_connection
    serial_connection -> serial_connection_low_level
    serial_connection_low_level -> connections
    serial_connection_low_level -> iserial_like
    socket_connection -> connections
    socket_connection -> raw_l2_socket_connection
    socket_connection -> raw_l3_socket_connection
    socket_connection -> ssl_socket_connection
    socket_connection -> tcp_socket_connection
    socket_connection -> udp_socket_connection
    ssl_socket_connection -> connections
    ssl_socket_connection -> tcp_socket_connection
    tcp_socket_connection -> connections
    tcp_socket_connection -> base_socket_connection
    udp_socket_connection -> connections
    udp_socket_connection -> base_socket_connection
    unix_socket_connection -> connections
    unix_socket_connection -> base_socket_connection

Loggers
-------

.. digraph:: boofuzz

    node[
        shape=record
        style=filled
		fillcolor=gray95
    ]
    size=10
    rankdir=LR;

    loggers -> fuzz_logger
    loggers -> fuzz_logger_csv
    loggers -> fuzz_logger_curses
    loggers -> fuzz_logger_db
    loggers -> fuzz_logger_postgres
    loggers -> fuzz_logger_text
    loggers -> ifuzz_logger
    loggers -> ifuzz_logger_backend
    fuzz_logger -> ifuzz_logger
    fuzz_logger_csv -> ifuzz_logger_backend
    fuzz_logger_curses -> ifuzz_logger_backend
    fuzz_logger_db -> ifuzz_logger_backend
    fuzz_logger_postgres -> ifuzz_logger_backend
    fuzz_logger_text -> ifuzz_logger_backend
    ifuzz_logger_backend -> ifuzz_logger


Monitors
--------

.. digraph:: boofuzz

    node[
        shape=record
        style=filled
		fillcolor=gray95
    ]
    size=10
    rankdir=LR;

    monitors -> base_monitor
    monitors -> callback_monitor
    monitors -> network_monitor
    monitors -> process_monitor
    callback_monitor -> base_monitor
    external_monitor -> base_monitor
    network_monitor -> base_monitor
    process_monitor -> base_monitor


Primitives 
----------

.. digraph:: boofuzz

    node[
        shape=record
        style=filled
		fillcolor=gray95
    ]
    size=10
    rankdir=LR;

    primitives -> base_primitive
    primitives -> bit_field
    primitives -> byte
    primitives -> bytes
    primitives -> delim
    primitives -> dword
    primitives -> float
    primitives -> from_file
    primitives -> group
    primitives -> mirror
    primitives -> multipledefault
    primitives -> qword
    primitives -> random_data
    primitives -> simple
    primitives -> static
    primitives -> string
    primitives -> word
    bit_field -> base_primitive
    byte -> bit_field
    bytes -> base_primitive
    delim -> string
    dword -> bit_field
    float -> base_primitive
    from_file -> base_primitive
    group -> base_primitive
    mirror -> base_primitive
    multipledefault -> base_primitive
    qword -> bit_field
    simple -> base_primitive
    static -> base_primitive
    string -> base_primitive
    word -> bit_field

Session
-------

.. digraph:: boofuzz

    node[
        shape=record
        style=filled
		fillcolor=gray95
    ]
    size=10
    rankdir=LR;

    sessions -> base_config
    sessions -> connection
    sessions -> session
    sessions -> session_info
    sessions -> target
    sessions -> web_app
    base_config -> callbacks
    base_config -> connections
    base_config -> session
    base_config -> target
    session -> boofuzz
    session -> blocks
    session -> constants
    session -> event_hook
    session -> exception
    session -> helpers
    session -> loggers
    session -> fuzz_logger
    session -> fuzz_logger_curses
    session -> fuzz_logger_db
    session -> fuzz_logger_text
    session -> monitors
    session -> mutation_context
    session -> pgraph
    session -> primitives
    session -> static
    session -> protocol_session
    session -> connection
    session -> session_info
    session -> target
    session -> web_app
    session -> app
    target -> connections
    web_app -> boofuzz
    web_app -> constants
    web_app -> app

Graph 
-----

.. digraph:: boofuzz

    node[
        shape=record
        style=filled
		fillcolor=gray95
    ]
    size=10
    rankdir=LR;

    E [label="edge"]
    G [label="graph"]
    N [label="node"]

    pgraph -> cluster
    pgraph -> E
    pgraph -> G
    pgraph -> N