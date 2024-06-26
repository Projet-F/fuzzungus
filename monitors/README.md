# Monitors

This folder contains the monitor scripts that are used to monitor the health of the target. They are supposed to be run on the target itself, and to send the data to the fuzzer.

## `process_monitor.py` and `process_monitor_unix.py`

Old monitors that have not been used in the 6 months of development, mainly because of the lack of the documentation. They are kept here for reference.

## `procmon.sh`

A "simple" (600 lines) shell script that monitors the target process. It is designed to run on a busybox, and so uses as few commands as possible. 
The code is big but fairly simple and well documented.