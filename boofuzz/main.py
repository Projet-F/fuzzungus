#!/usr/bin/env python3
"""Main script for fuzzungus"""

import argparse
import importlib.util
import os
import sys
import time
import shutil
import json
import warnings
import subprocess
from colorama import Fore, Style

import boofuzz

type Path = str

CLI_OPTION = None


def parse_arg(command_line=None) -> tuple[argparse.ArgumentParser, argparse.Namespace, argparse.ArgumentParser]:
    verbose_parser = argparse.ArgumentParser(add_help=False)
    verbose_parser.add_argument(
        '-v',
        help='Log level in shell. -v or -vv or -vvv',
        dest='verbose',
        action='count',
        default=0
    )
    save_dir_parser = argparse.ArgumentParser(add_help=False)
    save_dir_parser.add_argument(
        '-d', '--save-dir',
        help='Specify the save folder where all the data of the previous campaign are.',
        required=True
    )

    parser = argparse.ArgumentParser('./boo')

    subparsers = parser.add_subparsers(dest='command', metavar='COMMAND')

    # fuzz
    fuzz = subparsers.add_parser('fuzz', help='Start the fuzzer', parents=[verbose_parser])
    fuzz.add_argument(
        '-f', '--conf-file',
        help='Location of the campaign configuration file to be used',
        required=True
    )
    fuzz.add_argument(
        '-d', '--save-dir',
        help='Folder for saving fuzzing campaign results',
        default=None
    )

    # continue
    continue_ = subparsers.add_parser('continue', help='Continue a stop fuzzing campaign',
                                      parents=[verbose_parser, save_dir_parser])

    # replay
    replay = subparsers.add_parser('replay', help='Replay some test case of a fuzzing campaign',
                                   parents=[verbose_parser, save_dir_parser])
    replay.add_argument(
        '-r', '--round-type',
        help='Name of the phase to begin with',
        required=True,
        metavar='ROUND_TYPE',
        choices=boofuzz.constants.AVAILABLE_ROUND_TYPE
    )
    replay.add_argument(
        '-s', '--seed-index',
        help='Number of the first seed to be used',
        required=True,
        type=int
    )
    replay.add_argument(
        '-n', '--max-number-of-rounds',
        help='Number of round to send',
        type=int,
        default=None
    )

    # open
    open_ = subparsers.add_parser('open', help='Open the web interface for a fuzzing campaign',
                                  parents=[save_dir_parser])
    open_.add_argument(
        '--ui-port',
        help=f'Port on which to serve the web interface (default {boofuzz.constants.DEFAULT_WEB_UI_PORT})',
        type=int,
        default=boofuzz.constants.DEFAULT_WEB_UI_PORT
    )
    open_.add_argument(
        '--ui-addr',
        help=f"Address on which to serve the web interface (default {boofuzz.constants.DEFAULT_WEB_UI_ADDRESS}). "
             f"Set to empty string to serve on all interfaces.",
        type=str,
        default=boofuzz.constants.DEFAULT_WEB_UI_ADDRESS
    )

    # Postgres
    db_parser = subparsers.add_parser('db', help='Commands relative to database.')
    db_subparser = db_parser.add_subparsers(dest='db_command', metavar='DB_COMMAND')
    db_list_parser = db_subparser.add_parser('list', help='List all the previous campaign save in database')

    db_connect_parser = db_subparser.add_parser('connect', help='Open an sql shell for a previous campaign')
    db_connect_parser.add_argument(
        '-d', '--save-dir',
        help='Specify the save folder where all the data of the previous campaign are.',
        required=False,
        default=None
    )
    db_connect_parser.add_argument(
        '--db-name',
        help='Name of the database to open.',
        required=False,
        default=None
    )

    # ssh-copy-id
    ssh_copy_id_parser = subparsers.add_parser('ssh-copy-id',
                                               help='Copy the public ssh key of the container in the target.')
    ssh_copy_id_parser.add_argument(
        '-l', '--login',
        help='Specifies the user to log in as on the remote machine.',
        required=True
    )
    ssh_copy_id_parser.add_argument(
        '-H', '--host',
        help='Address of the remote host.',
        required=True
    )
    ssh_copy_id_parser.add_argument(
        '-p', '--port',
        help='Port to connect to on the remote host.',
        required=False,
        default=boofuzz.constants.DEFAULT_SSH_PORT,
        type=int
    )

    # open-shell
    open_shell_parser = subparsers.add_parser('open-shell',
                                              help='Open a bash shell in the container.')

    args = parser.parse_args(command_line)

    if args.command is None:
        parser.print_help()
        exit(2)

    return parser, args, db_parser


def get_module(campaign_file_path: Path, parser: argparse.ArgumentParser):
    """ This function import the campaign configuration file, so it can be used after in this script."""
    try:
        # https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
        file_path = campaign_file_path
        module_name = 'module'

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Now you can use `module` to access the functions and classes in the imported module
    except ImportError:
        parser.error(f'Error while importing the campaign configuration file "{campaign_file_path}".')
        # exit(2) -- (parser.error do the exit)

    return module


def get_save_dir(campaign_file_path: Path, parser: argparse.ArgumentParser, args: argparse.Namespace) -> (Path, str):
    """ This function create the folder where all the required data for a replay or a stop recovery will be saved. """
    if args.save_dir is None:
        parent_save_dir = os.path.join(os.getcwd(), boofuzz.constants.RESULTS_DIR)
    else:
        parent_save_dir = args.save_dir

    try:
        os.mkdir(parent_save_dir)
    except FileNotFoundError:
        parser.error(f'The folder for saving fuzzing result cannot be created because a parent directory in the path'
                     f'does not exist. Dir : "{parent_save_dir}".')
        # exit(2) -- (parser.error do the exit)
    except FileExistsError:
        pass
    except PermissionError:
        parser.error(f'Permission denied for create the folder "{parent_save_dir}"')
        # exit(2) -- (parser.error do the exit)
    except OSError:
        raise

    campaign_id = boofuzz.get_datetime() + '_' + os.path.basename(campaign_file_path).removesuffix('.py')
    save_dir_path = os.path.join(parent_save_dir, campaign_id)

    try:
        os.mkdir(save_dir_path)
    except FileNotFoundError:
        # We create parent directory before so this code should not be reach
        raise
    except FileExistsError:
        parser.error(f'Folder "{save_dir_path}" already exist, wait 1 second before relaunch the program')
        # exit(2) -- (parser.error do the exit)
    except PermissionError:
        parser.error(f'Permission denied for create the folder "{save_dir_path}"')
        # exit(2) -- (parser.error do the exit)
    except OSError:
        raise

    return save_dir_path, campaign_id


def save_dir_setup(save_dir_path: Path, campaign_file_path: Path, campaign_id: str, args: argparse.Namespace,
                   parser: argparse.ArgumentParser) -> Path:
    """ This function save all the required data for a replay or a stop recovery. """
    try:
        save_campaign_file_path: Path = shutil.copy(campaign_file_path, save_dir_path)  # Copy conf file for replay
    except FileNotFoundError:
        parser.error(f'The file {campaign_file_path} seem to not exist')
    except PermissionError:
        parser.error(f'The file {campaign_file_path} is not readable')
    except OSError:
        raise

    # Save cli option for replayability
    json_path = get_json_path(save_dir_path)

    json_dict = vars(args)
    json_dict['campaign_id'] = campaign_id

    with open(json_path, 'w') as f:
        json.dump(json_dict, f, indent=4)

    return save_campaign_file_path


def get_db_names(campaign_id: str, args: argparse.Namespace) -> (str, str):
    db_name = campaign_id

    if args.command in ['fuzz', 'continue', 'open', 'db']:
        db_table_name = None
    elif args.command == 'replay':
        db_table_name = 'replay_' + boofuzz.get_datetime()
    else:
        raise Exception('This code should not be reach due to previous check.')

    if len(db_name) > boofuzz.constants.DB_MAX_IDENTIFIERS_LEN:
        db_name = db_name[:boofuzz.constants.DB_MAX_IDENTIFIERS_LEN]
        warnings.warn('Variable db_name too long')

    if db_table_name is not None and len(db_table_name) > boofuzz.constants.DB_MAX_IDENTIFIERS_LEN:
        db_table_name = db_table_name[:boofuzz.constants.DB_MAX_IDENTIFIERS_LEN]
        warnings.warn('Variable db_table_name too long')

    return db_name, db_table_name


def get_session(save_dir_path: Path, campaign_id: str, module, args: argparse.Namespace) -> boofuzz.BaseConfig:
    """
        This function call the Config class in the campaign configuration file to initialize the boofuzz.Session.
        It also in charge of the stop recovery process.
    """
    assert args.command in ['fuzz', 'continue', 'replay']

    db_name, db_table_name = get_db_names(campaign_id, args)

    # Create the session thanks to config functions in the conf file
    # sys.path.insert(0, save_dir_path)  # Old way to import callbacks in boofuzz.BaseConfig
    config_module: boofuzz.BaseConfig = module.Config(campaign_folder=save_dir_path, log_level_stdout=args.verbose,
                                                      db_name=db_name, db_table_name=db_table_name)
    # sys.path.remove(save_dir_path)  # Old way to import callbacks in boofuzz.BaseConfig

    config_module.session_init()

    config_module.config()

    config_module.session.nominal_recv_test = config_module.nominal_recv_test

    if args.command == 'fuzz':
        pass
    elif args.command == 'continue':
        with boofuzz.FuzzLoggerPostgresReader(db_name, db_table_name) as reader:
            round_type, seed_index, mutant_index = reader.get_data_for_continue_command()

        config_module.session.round_type = round_type
        config_module.session.seed_index = seed_index
        config_module.session.total_mutant_index = mutant_index - 1
    elif args.command == 'replay':
        if args.round_type is not None:
            config_module.session.round_type = args.round_type
        if args.seed_index is not None:
            config_module.session.seed_index = args.seed_index
        if args.max_number_of_rounds is not None:
            config_module.session.max_number_of_rounds = args.max_number_of_rounds

    config_module.config_nominal()

    return config_module


def get_json_path(save_dir_path: Path) -> Path:
    """ This function return the path where the json file is. """
    return os.path.join(save_dir_path, boofuzz.constants.CONF_NAME)


def read_from_json(save_dir_path: Path, parser: argparse.ArgumentParser) -> dict:
    """ This function return the dictionary from the json file. """
    json_path = get_json_path(save_dir_path)
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        parser.error(f'The file {json_path} is not found.\n'
                     f'Maybe --save-dir is misspell.')


def get_save_campaign_file_path(json_dict: dict, save_dir_path: Path) -> Path:
    """ This function use the data in the json file to return the save campaign configuration path. """
    return os.path.join(save_dir_path, os.path.basename(json_dict['conf_file']))


def open_file(campaign_id: str, args: argparse.Namespace) -> None:
    """This function reopen the web interface after the campaign was close. It's an easy way to view logs."""
    db_name, db_table_name = get_db_names(campaign_id, args)

    boofuzz.sessions.open_test_run(db_name=db_name, db_table_name=db_table_name,
                                   port=args.ui_port, address=args.ui_addr)

    print("Serving web page at http://{0}:{1}. Hit Ctrl+C to quit.".format(args.ui_addr, args.ui_port))
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('Ctrl+C')


def db_list() -> None:
    """This function print the db_name and db_size of each database"""
    with boofuzz.FuzzLoggerPostgresReader(boofuzz.constants.DB_DEFAULT_NAME) as reader:
        for db_name, db_size in reader.get_datname_and_db_size():
            print(f'{Fore.GREEN}{db_name:{boofuzz.constants.DB_MAX_IDENTIFIERS_LEN}} '  # max size of identifiers
                  f'{Fore.BLUE}{db_size}{Style.RESET_ALL}')


def db_connect(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """This function call the open_cli_connection() function who let user
    type sql command directly in Postgres database."""
    if args.db_name:
        db_name = args.db_name
    elif args.save_dir:
        save_dir_path = args.save_dir
        json_dict = read_from_json(save_dir_path, parser)
        campaign_id = json_dict['campaign_id']
        db_name, db_table_name = get_db_names(campaign_id, args)
    else:
        db_name = None
    boofuzz.FuzzLoggerPostgresReader.open_cli_connection(db_name)


def ssh_copy_id(args: argparse.Namespace) -> None:
    """This function copy the public ssh key of the container in the target."""
    subprocess.run(['ssh-copy-id',
                    '-p', str(args.port),
                    f'{args.login}@{args.host}'])


def open_shell() -> None:
    """Function to open a shell. Useful to quickly open a bash shell in a container."""
    subprocess.run(['bash'])


def main() -> None:
    """ Main function of this script who called all the other functions. """
    parser, args, db_parser = parse_arg(CLI_OPTION)

    if args.command == 'fuzz':
        campaign_file_path = args.conf_file
        save_dir_path, campaign_id = get_save_dir(campaign_file_path, parser, args)
        save_campaign_file_path = save_dir_setup(save_dir_path, campaign_file_path, campaign_id, args, parser)
    elif args.command in ['continue', 'replay', 'open']:
        campaign_file_path = None
        save_dir_path = args.save_dir
        json_dict = read_from_json(save_dir_path, parser)
        campaign_id = json_dict['campaign_id']
        save_campaign_file_path = get_save_campaign_file_path(json_dict, save_dir_path)
    elif args.command == 'db':
        if args.db_command == 'list':
            db_list()
            exit(0)
        elif args.db_command == 'connect':
            db_connect(args, parser)
            exit(0)
        else:
            print('error : The command after db is missing.\n', file=sys.stderr)
            db_parser.print_help()
            exit(2)
    elif args.command == 'ssh-copy-id':
        ssh_copy_id(args)
        exit(0)
    elif args.command == 'open-shell':
        open_shell()
        exit(0)
    else:
        raise Exception('This code should not be reach due to previous check.')

    if args.command == 'open':
        open_file(campaign_id, args)
        exit(0)

    module = get_module(save_campaign_file_path, parser)

    config_module = get_session(save_dir_path, campaign_id, module, args)

    if args.command == 'fuzz':
        # Graph generation
        config_module.graph_generation(graph_name=os.path.join(save_dir_path, boofuzz.constants.GRAPH_NAME))

    if config_module.fuzz:
        try:
            config_module.session.fuzz_indefinitely()
        except KeyboardInterrupt:
            pass  # KeyboardInterrupt is the normal way to stop the fuzzer. So don't raise an error.


if __name__ == '__main__':
    main()
