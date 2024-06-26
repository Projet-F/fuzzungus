.. _main:

Main File
=========

The main file is the entry point of Fuzzungus.

It is the file responsible for storing all the data necessary to restart the fuzzer after a stop. (An error for example.)

To execute this file with docker do ``./boo``.

If you didn't use docker, do ``python boofuzz/main.py`` instead.

Help
----

Use the `-\-help` (or `-h`) option to get an explanation of all commands.

Example
^^^^^^^

.. code-block:: bash

    $ ./boo -h
    $ ./boo --help

    $ ./boo fuzz -h
    $ ./boo continue -h
    $ ./boo replay -h
    $ ./boo open -h

    $ ./boo db -h
    $ ./boo db connect -h

    $ ./boo ssh-copy-id -h
    $ ./boo open-shell -h

Verbose
-------

You can use the `-v` option multiple times to increase the logging level.

See :ref:`logging`.

Fuzz
----

Start the fuzzer.

Options
^^^^^^^

-\-conf-file
""""""""""""

The `-\-conf-file` or (`-f`) option is the location of the campaign configuration file.

-\-save-dir
"""""""""""

The `-\-save-dir` (or `-d`) option is use to set the location of the save folder that contains all the data from the previous campaign.

.. warning::
    If you use docker, don't use this option.

Examples
^^^^^^^^

.. code-block:: bash

    $ ./boo fuzz -f configuration-files/tftp/tftp_advanced_demo.py -vvv

Continue
--------

Thanks to the database, it's easy to resume an old fuzzing session that was stopped a long time ago.

Options
^^^^^^^

-\-save-dir
"""""""""""

The `-\-save-dir` (or `-d`) option is use to set the location of the save folder that contains all the data from the previous campaign.

Example
^^^^^^^

.. code-block:: bash

    $ ./boo continue -d ./fuzzungus-results/2024-06-10T09:30:19_tftp_advanced_demo -vv

Replay
------

Thanks to the database, it's also easy to replay some test cases without having to redo all the previous ones.

In fact, you can specify a witch `round type` and `seed` that you want to start with.

When you are in replay mode, all logs are stored in a different table. So it will be easy to access them later.

Options
^^^^^^^

-\-save-dir
"""""""""""

The `-\-save-dir` (or `-d`) option is use to set the location of the save folder that contains all the data from the previous campaign.

-\-round-type
"""""""""""""

Specify with `-\-round-type` (or `-r`) at which `round-type` you want to start fuzzing (`library` or `random_mutation` or `random_generation`).

-\-seed-index
"""""""""""""

Specify with `-\-seed-index` (or `-s`) at which `seed-index` you want to start fuzzing.

-\-max-number-of-rounds
"""""""""""""""""""""""

This optional option could be used if you want the fuzzer to stop automatically after n rounds.

But you can also don't use this option and press `ctrl+c` to stop the replay.

`-n` is an alias for this option.

Example
^^^^^^^

.. code-block:: bash

    $ ./boo replay -d fuzzungus-results/2024-06-10T09:30:19_tftp_advanced_demo -r random_mutation -s 30 -n 10

Open
----

During a campaign, you can access the web front-end at `127.0.0.1:26000`.

And, thanks to the logging system, you can also access to the web front-end after with the open command.

Options
^^^^^^^

-\-save-dir
"""""""""""

The `-\-save-dir` (or `-d`) options is use to set the location of the save folder that contains all the data from the previous campaign.

-\-ui-port
""""""""""

Optional option to change the port. Default to `26000`.

Useful if you want to open more than on previous campaign at the same time.

-\-ui-addr
""""""""""

Optional option to change the address. Default to `127.0.0.1`.

Example
^^^^^^^

.. code-block:: bash

    $ ./boo open -d fuzzungus-results/2024-06-10T09:30:19_tftp_advanced_demo

Db list
-------

This command list all databases present in the Postgres and their size.

Each database correspond with a campaign.

Options
^^^^^^^

This command didn't have any option.

Example
^^^^^^^

.. code-block:: bash

    $ ./boo db list

Db connect
----------

This command open a Postgres shell in a database.

You can directly paste sql command to see the result.

Options
^^^^^^^

You can use this command without any option and it will open a shell in the default database. (`fuzz`)

-\-save-dir
"""""""""""

The `-\-save-dir` (or `-d`) option is use to set the location of the save folder that contains all the data from the previous campaign.

With this option, the shell will directly open in the database of this campaign.

-\-db-name
""""""""""

Use `-\-db-name` to directly connect to a specific database.

Useful after ``./boo db list``.

Example
^^^^^^^

.. code-block:: bash

    $ ./boo db connect

    $ ./boo db connect -d fuzzungus-results/2024-06-10T09:30:19_tftp_advanced_demo

    $ ./boo db connect --db-name 2024-06-10T09:30:19_tftp_advanced_demo

Ssh-copy-id
-----------

This command copy the public ssh key of the docker container in the target.

Thanks to this key, you can use the busybox procmon.

Indeed, this process monitor use an ssh connection to retrieve data from the target. So, the key is mandatory to bypass the password.

Options
^^^^^^^

-\-login
""""""""

The `-\-login` (or `-l`) option is use to specifies the user to log in as on the remote machine.

-\-host
"""""""

The `-\-host` (or `-H`) option is use to specifies the address of the remote host.

-\-port
"""""""

The optional `-\-port` (or `-p`) option is use to specifies the port to connect to on the remote host.

Default to 22.

Example
^^^^^^^

.. code-block:: bash

    $ ./boo ssh-copy-id -l kali -H 172.1.1.15 -p 3000

Open-shell
----------

This command open a bash shell in the docker container.

Options
^^^^^^^

This command didn't have any option.

Example
^^^^^^^

.. code-block:: bash

    $ ./boo open-shell
