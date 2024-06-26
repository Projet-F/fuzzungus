.. _callgraph:

Callgraph
=========

The goal of this section is to represent a basic callgraph of the functions for a fuzzing section, to give a general understanding of the codebase.
We focused on the :class:`Session` class, as it is at the same time the main class of the fuzzer, and the, by far, biggest one.

Were not represented : 

- Every logging methods 
- Built-in python methods

:meth:`session.fuzz_indefinitely`
---------------------------------

Initialization calls from the :meth:`session.fuzz_indefinitely` method, that fuzzes round by round, to the :meth:`_main_fuzz_loop` method.

.. digraph:: fuzz_indefinitely

    node[shape=record]
    size="15"
    nodesep=1


    FI [color=Red,label="session.fuzz_indefinitely"];
    CTR [label="session.calculate_total_round"];
    F [label="session.fuzz"];
    CMNR [label="session.check_max_number_of_rounds"];
    MFL [color=Red,label="session._main_fuzz_loop"];
    NM [label="session.num_mutations"];
    NMR [label="session._num_mutations_recursive"];
    EF [label="session.edges_from"];
    FSNBYP [label="session._fuzz_single_node_by_path"];
    PNTE [label="session._path_names_to_edges"];

    FI -> {CTR F CMNR};
    F -> {MFL NM} [label="If fuzz the entire graph"];
    F -> {FSNBYP PNTE MFL} [label="If fuzz one request"];
    NM -> NMR;
    NMR -> EF;
    NMR -> NMR;


:meth:`session._main_fuzz_loop`
-------------------------------

New graph for the calls from the :meth:`session._main_fuzz_loop` method, as it is the main loop of the fuzzer, and so, the one with the biggest callgraph.

.. digraph:: fuzz_indefinitely

    node[shape=record]
    size="20"
    nodesep=1

    MFL [color=Red,label="session._main_fuzz_loop"];
    SI [label="session.server_init"];
    ST [label="session._start_target"];
    BST [label="BaseMonitor.start_target"];
    BPST [label="BaseMonitor.post_start_target"];
    TO [label="target.open"];
    GMI [label="session._generate_mutations_indefinitely"];
    GTCFNM [label="session._generate_test_case_from_named_mutations"];
    RT [label="session._restart_target"];
    FCC [color=Red,label="session._fuzz_current_case"];
    NT [label="session.nominal_test"];
    SEF [label="session.export_file"];
    TC [label="target.close"];

    MFL -> {SI ST TO};
    ST -> {BST BPST}; 
    MFL -> GMI [label="If fuzz the entire graph"]; 
    MFL -> GTCFNM [label="If fuzz one request"];
    MFL ->RT [label="If restart interval reached"];
    MFL -> FCC
    MFL -> NT [label="If nominal test interval reached"];
    MFL -> SEF [label="If exception"];
    MFL -> TC


:meth:`session._fuzz_current_case`
----------------------------------

.. digraph:: fuzz_current_case

    node[shape=record]
    size="20"
    nodesep=1

    FCC [color=Red,label="session._fuzz_current_case"];
    PIFP [label="session._pause_if_pause_flag_is_set"];
    TCN [label="session._test_case_name"];
    GNM [label="session.get_num_mutations"];
    NM [label="session.num_mutations"];
    OC [label="session._open_connection_keep_trying"];
    TO [label="target.open"];
    RT [label="session._restart_target"];
    PS [label="session._pre_send"];
    BMPS [label="BaseMonitor.pre_send"];
    CCN [label="session._callback_current_node"];
    FC [color=Red,label="session.fragmentation_check"];
    CFPDT [label="session._check_for_passively_detected_failures"];
    TC [label="target.close"];
    SS [label="session._sleep"];
    PF [label="session._process_failures"];
    EF [label="session.export_file"];

    FCC -> {PIFP TCN GNM OC PS CCN FC CFPDT};
    FCC -> TC [label="If not reuse target connection"];
    FCC -> SS [label="If sleep between tests"];
    FCC -> PF [label="Except failure"];
    FCC -> EF [label="Except failure"];
    GNM -> NM;
    OC -> {TO RT};
    PS -> BMPS;

:meth:`session.fragmentation_check`
-----------------------------------

.. digraph:: fuzz_current_case

    node[shape=record]
    size="20"
    nodesep=1

    FC [color=Red,label="session.fragmentation_check"];
    TA [label="session.transmit_all"];
    TN [label="session.transmit_normal"];
    TF [label="session.transmit_fuzz"];
    RCTO [label="request.calculate_rto"];
    RR [label="request.render"];
    TS [label="target.send"];
    TGC [label="target.get_connection"];
    TR [label="target.recv"];
    
    FC -> TA;
    TA -> TN [label="If transmit normal"];
    TA -> TF [label="If transmit fuzz"];
    TA -> RCTO;
    TN -> {RR TS TGC TR};
    TF -> {RR TS TGC TR};