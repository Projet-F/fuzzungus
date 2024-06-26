#!/usr/bin/env python3
"""Demo FTP fuzzer as a standalone script."""

from boofuzz import *

import time


def main():
    """
    This example is a very simple FTP fuzzer. It uses no process monitory
    (procmon) and assumes that the FTP server is already running.
    """
    session = Session(target=Target(connection=TCPSocketConnection("172.23.1.131", 21)),
        receive_data_after_fuzz=True)
    session.targets.append(session.targets[0])
    
    define_proto(session=session)
    session.fuzz(max_depth=2)

def ParserPortPASV(target,_fuzz_data_logger,session,node,edge,test_case_context):
    i = 0
    while("227" not in str(session.last_recv,encoding='utf-8')):
        session.last_recv = session.targets[0].recv()
    while(session.last_recv[i]!=ord('(')):
        i=i+1
    i=i+1
    for u in range(4):
        while(session.last_recv[i]!=ord(',')):
            i=i+1
        i=i+1
    j=i
    while(session.last_recv[j]!=ord(',')):
        j=j+1
    port = int(session.last_recv[i:j])*256
    i=j+1
    j=i
    while(session.last_recv[j]!=ord(')')):
        j=j+1
    port = port + int(session.last_recv[i:j])
    session.targets[1]=Target(connection=TCPSocketConnection("127.0.0.1", int(port)))
    session.targets[1].set_fuzz_data_logger(session.targets[0]._fuzz_data_logger)
    session.targets[1].open()

def ControlToData(target,_fuzz_data_logger,session,node,edge,test_case_context):
    session.target_to_use = 1


def DataToControl(target,_fuzz_data_logger,session,node,edge,test_case_context):
    session.targets[session.target_to_use].close()
    session.target_to_use = 0

def ReadData(target,_fuzz_data_logger,session,node,edge,test_case_context):
    session.target_to_use = 1
    data = session.targets[session.target_to_use].recv()
    while(len(data)!=0):
        data = session.targets[session.target_to_use].recv()
    session.target_to_use = 0

def Clear(target,_fuzz_data_logger,session,node,edge,test_case_context):
    if(session.target_to_use==1):
        session.targets[session.target_to_use].close()
        session.target_to_use=0
    session.targets[session.target_to_use].open()
        






# See https://datatracker.ietf.org/doc/html/rfc959#autoid-4
def define_proto(session):
    # disable Black formatting to keep custom indentation
    # fmt: off

    # ACCESS CONTROL COMMANDS
    user = Request("user", children=(
        String(name="key", default_value="USER", fuzzable=False),
        Delim(name="space", default_value=" ", fuzzable=False),
        String(name="val", default_value="anonymous", fuzzable=False),
        Static(name="end", default_value="\r\n"),
    ))

    passw = Request("pass", children=(
        Static(name="key", default_value="PASS"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="",fuzzable=False),
        Static(name="end", default_value="\r\n"),
    ))

    acct = Request("acct", children=(
        Static(name="key", default_value="ACCT"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="AAAA"), # telnet identifier
        Static(name="end", default_value="\r\n"),
    ))

    cwd = Request("cwd", children=(
        Static(name="key", default_value="CWD"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="/",fuzzable=True),
        Static(name="end", default_value="\r\n"),
    ))
    cwd2 = Request("cwd2", children=(
        Static(name="key", default_value="CWD"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="TESTFTP",fuzzable=False),
        Static(name="end", default_value="\r\n"),
    ))

    cdup = Request("cdup", children=(
        Static(name="key", default_value="CDUP"),
        Static(name="end", default_value="\r\n"),
    ))

    smnt = Request("smnt", children=(
        Static(name="key", default_value="SMNT"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="AAAA",fuzzable=True), # pathname directory
        Static(name="end", default_value="\r\n"),
    ))

    rein = Request("rein", children=(
        Static(name="key", default_value="REIN"),
        Static(name="end", default_value="\r\n"),
    ))

    quit = Request("quit", children=(
        Group(name="key",values=["QUIT","QUIT"]),
        Static(name="end", default_value="\r\n"),
    ))

    # TRANSFER PARAMETER COMMANDS
    # TODO : set fuzzing IP as default value and don't fuzz it
    port = Request("port", children=(
        Static(name="key", default_value="PORT"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="h1", default_value="127",fuzzable=False),
        Delim(name="comma1", default_value=",",fuzzable=False),
        String(name="h2", default_value="0",fuzzable=False),
        Delim(name="comma2", default_value=",",fuzzable=False),
        String(name="h3", default_value="0",fuzzable=False),
        Delim(name="comma3", default_value=",",fuzzable=False),
        String(name="h4", default_value="1",fuzzable=False),
        Delim(name="comma4", default_value=",",fuzzable=False),
        String(name="p1", default_value="10",fuzzable=False),
        Delim(name="comma5", default_value=",",fuzzable=False),
        String(name="p2", default_value="21",fuzzable=False),
        Static(name="end", default_value="\r\n"),
    ))

    pasv = Request("pasv", children=(
        Static(name="key", default_value="PASV"),
        Static(name="end", default_value="\r\n"),
    ))

    pasv2 = Request("pasv2", children=(
        Static(name="key", default_value="PASV"),
        Static(name="end", default_value="\r\n"),
    ))

    type = Request("type", children=(
        Static(name="key", default_value="TYPE"),
        Delim(name="space", default_value=" ",fuzzable=False),
        Group(name="val", values=["A","E","I","N","T","C","L"]), # A=ASCII, E=EBCDIC, I=image, N=non-print, T=telnet, C=carriage control, L <byte size>=local byte size
        Static(name="end", default_value="\r\n"),
    ))

    stru = Request("stru", children=(
        Static(name="key", default_value="STRU"),
        Delim(name="space", default_value=" ",fuzzable=False),
        Group(name="val", values=["F","R","P"]), # F=file, R=record, P=page
        Static(name="end", default_value="\r\n"),
    ))

    mode = Request("mode", children=(
        Static(name="key", default_value="MODE"),
        Delim(name="space", default_value=" ",fuzzable=False),
        Group(name="val", values=["S","B","C"]), # S=stream, B=block, C=compressed
        Static(name="end", default_value="\r\n"),
    ))

    # FTP SERVICE COMMANDS
    retr = Request("retr", children=(
        Static(name="key", default_value="RETR"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="AAAA",fuzzable=True),
        Static(name="end", default_value="\r\n"),
    ))

    stor = Request("stor", children=(
        Static(name="key", default_value="STOR"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="AAAA",fuzzable=True),
        Static(name="end", default_value="\r\n"),
    ))

    stou = Request("stou", children =(
        Static(name="key", default_value="STOU"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="AAAA",fuzzable=True),
        Static(name="end", default_value="\r\n"),
    ))

    appe = Request("appe", children=(   
        Static(name="key", default_value="APPE"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="AAAA",fuzzable=True),
        Static(name="end", default_value="\r\n"),
    ))

    allo = Request("allo", children=(
        Static(name="key", default_value="ALLO"),
        Delim(name="space", default_value=" ",fuzzable=False),
        Group(name="val", values=["250","1545","5645"]),
        Static(name="end", default_value="\r\n"),
    ))

    rest = Request("rest", children=(
        Static(name="key", default_value="REST"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="AAAA",fuzzable=True), # marker
        Static(name="end", default_value="\r\n"),
    ))

    rnfr = Request("rnfr", children=(
        Static(name="key", default_value="RNFR"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="AAAA",fuzzable=True),
        Static(name="end", default_value="\r\n"),
    ))

    rnto = Request("rnto", children=(
        Static(name="key", default_value="RNTO"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="AAAA-test",fuzzable=True),
        Static(name="end", default_value="\r\n"),
    ))

    abor = Request("abor", children=(
        Static(name="key", default_value="ABOR"),
        Static(name="end", default_value="\r\n"),
    ))

    dele = Request("dele", children=(
        Static(name="key", default_value="DELE"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="AAAA",fuzzable=True),
        Static(name="end", default_value="\r\n"),
    ))

    rmd = Request("rmd", children=(
        Static(name="key", default_value="RMD"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="AAAA",fuzzable=True),
        Static(name="end", default_value="\r\n"),
    ))

    mkd = Request("mkd", children=(
        Static(name="key", default_value="MKD"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="AAAA",fuzzable=True),
        Static(name="end", default_value="\r\n"),
    ))

    pwd = Request("pwd", children=(
        Static(name="key", default_value="PWD"),
        Static(name="end", default_value="\r\n"),
    ))

    list = Request("list", children=(
        Static(name="key", default_value="LIST"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="pathname", default_value="",fuzzable=False),
        Static(name="end", default_value="\r\n"),
    ))

    nlst = Request("nlst", children=(
        Static(name="key", default_value="NLST"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="pathname", default_value="",fuzzable=True),
        Static(name="end", default_value="\r\n"),
    ))

    site = Request("site", children=(
        Static(name="key", default_value="SITE"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="AAAA",fuzzable=True),
        Static(name="end", default_value="\r\n"),
    ))

    syst = Request("syst", children=(
        Static(name="key", default_value="SYST"),
        Static(name="end", default_value="\r\n"),
    ))

    stat = Request("stat", children=(
        Static(name="key", default_value="STAT"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="val", default_value="",fuzzable=True),
        Static(name="end", default_value="\r\n"),
    ))

    help = Request("help", children=(
        Static(name="key", default_value="HELP"),
        Delim(name="space", default_value=" ",fuzzable=False),
        String(name="command", default_value="list",fuzzable=True),
        Static(name="end", default_value="\r\n"),
    ))

    noop = Request("noop", children=(
        Static(name="key", default_value="NOOP"),
        Static(name="end", default_value="\r\n"),
    ))
    # fmt: on

    daataa = Request("data",children=(
        String(name="val", default_value="",fuzzable=True),
        Static(name="fin", default_value="\r\n"),
    ))


    session.connect(user,callback=Clear)
    session.connect(user, passw)
    session.connect(passw, site)
    session.connect(passw, syst)
    session.connect(passw, stat)
    session.connect(passw, help)
    session.connect(passw, noop)
    session.connect(passw, acct)
    session.connect(passw, cwd)
    session.connect(passw, cdup)
    session.connect(passw, smnt)
    session.connect(passw, rein)
    session.connect(passw, quit)
    session.connect(passw, port)

    session.connect(passw, cwd2)
    session.connect(cwd2, pasv)

    session.connect(pasv, type,callback=ParserPortPASV)
    session.connect(type, stru)
    session.connect(stru, mode)

    session.connect(mode, stou)
    session.connect(stou, daataa,callback=ControlToData)
    session.connect(daataa,quit,callback=DataToControl)
    
    session.connect(mode, appe)
    session.connect(appe, daataa,callback=ControlToData)
    session.connect(daataa,quit,callback=DataToControl)

    session.connect(mode, allo)
    session.connect(allo, stor)
    session.connect(stor,daataa,callback=ControlToData)
    session.connect(daataa,quit,callback=DataToControl)
    
    session.connect(mode, rest)
    
    session.connect(mode, mkd)
    session.connect(mode, pwd)
    session.connect(mode, list)
    session.connect(list,pasv2,callback=ReadData)
    session.connect(pasv2, retr,callback=ParserPortPASV)
    session.connect(retr,quit,callback=ReadData)
    
    session.connect(list, rnfr,callback=ReadData)
    session.connect(rnfr, rnto)
    session.connect(rnto,quit)

    session.connect(list, dele,callback=ReadData)
    session.connect(list, rmd,callback=ReadData)
    session.connect(mode, nlst)
    session.connect(nlst,quit,callback=ReadData)



if __name__ == "__main__":
    main()
