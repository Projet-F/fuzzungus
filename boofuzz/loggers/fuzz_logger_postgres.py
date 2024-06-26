import collections
import datetime
import psycopg
import psycopg.sql
import os
import subprocess
from typing import Generator
from colorama import Fore, Style

import boofuzz.constants
from boofuzz import data_test_case, data_test_step
from boofuzz.loggers.ifuzz_logger_backend import IFuzzLoggerBackend

type Path = str


def get_time_stamp():
    return datetime.datetime.now(datetime.UTC).isoformat()


def get_db_socket_path() -> Path:
    """Return the absolute path of the unix socket"""
    inside_docker = os.getenv('INSIDE_DOCKER', False)

    if inside_docker:
        abs_db_socket_path = '/var/run/postgresql/'
    else:
        # Get this file path
        file_path = os.path.abspath(__file__)
        # Strip the file name and the last two directory from the path
        dir_path = os.path.dirname(os.path.dirname(os.path.dirname(file_path)))
        # Add db_socket to the path
        abs_db_socket_path = os.path.join(dir_path, "db_socket")

    return abs_db_socket_path


def _get_test_case_data(database_connection: psycopg.Connection, table_cases_name: str, table_steps_name: str,
                        index: int) -> data_test_case.DataTestCase | None:
    c = database_connection.cursor()

    c.execute(
        psycopg.sql.SQL(
            """SELECT name, number, timestamp FROM {} WHERE number=%s LIMIT 1"""
        ).format(psycopg.sql.Identifier(table_cases_name)),
        (
            index,
        )
    )
    test_case_row = c.fetchone()
    if test_case_row is None:
        return None

    c.execute(
        psycopg.sql.SQL(
            """SELECT type, description, data, timestamp, is_truncated FROM {}
               WHERE test_case_index=%s"""
        ).format(psycopg.sql.Identifier(table_steps_name)),
        (
            index,
        )
    )
    rows = c.fetchall()
    steps = []
    for row in rows:
        steps.append(
            data_test_step.DataTestStep(
                type=row[0], description=row[1], data=row[2], timestamp=row[3].isoformat(), truncated=row[4]
            )
        )

    return data_test_case.DataTestCase(
        name=test_case_row[0], index=test_case_row[1], timestamp=test_case_row[2].isoformat(), steps=steps
    )


def verify_name_len(db_name: str, db_table_name: str | None):
    """Verify that len of identifiers are good for postgres."""
    if len(db_name) > boofuzz.constants.DB_MAX_IDENTIFIERS_LEN:
        raise Exception(f'len of db_name boofuzz.loggers.fuzz_logger_postgres.'
                        f'{len(db_name)=}')

    if db_table_name is not None and len(db_table_name) > boofuzz.constants.DB_MAX_IDENTIFIERS_LEN - 6:
        # minus 6 because max(len('_cases'), len('_steps')) = 6
        raise Exception(f'len of db_table_name too long in boofuzz.loggers.fuzz_logger_postgres.'
                        f'{len(db_table_name)=}')


class FuzzLoggerPostgres(IFuzzLoggerBackend):
    """
    Log fuzz data in a PostgreSQL database.
    Using an existing database requires more graceful exits to prevent case number duplication.

    Args:
        db_name (str):       Name of the database.
        db_table_name (str | None): Name of tables in database. Default "".
        num_log_cases (int): Minimize disk usage by only saving passing test cases
                             if they are in the n test cases preceding a failure or error.
                             Set to 0 to save after every test case (high disk I/O!). Default 0.
    """

    def __init__(self, db_name: str, db_table_name: str | None = None, num_log_cases=0):
        verify_name_len(db_name, db_table_name)

        abs_db_socket_path = get_db_socket_path()

        db_connection = psycopg.connect(
            host=abs_db_socket_path,
            dbname=boofuzz.constants.DB_DEFAULT_NAME,
            user=boofuzz.constants.DB_USER_NAME,
            password=boofuzz.constants.DB_PASSWORD
        )

        db_connection.autocommit = True

        db_cursor = db_connection.cursor()

        try:
            db_cursor.execute(
                psycopg.sql.SQL(
                    """CREATE DATABASE {}"""
                ).format(psycopg.sql.Identifier(db_name))
            )
        except psycopg.errors.DuplicateDatabase:
            pass
        finally:
            db_cursor.close()
            del db_cursor
            db_connection.close()
            del db_connection

        self._db_connection = psycopg.connect(
            host=abs_db_socket_path,
            dbname=db_name,
            user=boofuzz.constants.DB_USER_NAME,
            password=boofuzz.constants.DB_PASSWORD
        )
        self._db_cursor = self._db_connection.cursor()

        self._db_cursor.execute("SET timezone = 'UTC'")

        self._table_cases_name = 'cases' if db_table_name is None else db_table_name + '_cases'
        self._db_cursor.execute(
            psycopg.sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {} (
                id                 SERIAL        NOT NULL       PRIMARY KEY,
                name               TEXT          NOT NULL,
                number             INTEGER       NOT NULL,
                round_type         TEXT,
                seed               TEXT,
                seed_index         INTEGER,
                timestamp          TIMESTAMP     NOT NULL)
                """
            ).format(psycopg.sql.Identifier(self._table_cases_name))
        )

        self._table_steps_name = 'steps' if db_table_name is None else db_table_name + '_steps'
        self._db_cursor.execute(
            psycopg.sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {} (
                id                 SERIAL        NOT NULL       PRIMARY KEY,
                test_case_index    INTEGER       NOT NULL,
                type               TEXT          NOT NULL,
                description        TEXT          NOT NULL,
                data               BYTEA         NOT NULL,
                is_truncated       BOOLEAN       NOT NULL,
                timestamp          TIMESTAMP     NOT NULL)
                """
            ).format(psycopg.sql.Identifier(self._table_steps_name))
        )

        self._db_connection.commit()

        self._current_test_case_index = 0

        self._queue = collections.deque([])  # Queue that holds last n test cases before commiting
        self._queue_max_len = num_log_cases
        self._problem_detected = False
        self._log_first_case = True
        self._data_truncate_length = 512

    def get_test_case_data(self, index: int) -> data_test_case.DataTestCase:
        return _get_test_case_data(self._db_connection, self._table_cases_name, self._table_steps_name, index)

    def open_test_case(self, test_case_id, name, index, round_type=None, seed=None, seed_index=None, *args, **kwargs):
        self._queue.append(
            [
                psycopg.sql.SQL(
                    """INSERT INTO {} (name, number, round_type, seed, seed_index, timestamp)
                       VALUES(%s, %s, %s, %s, %s, %s)"""
                ).format(psycopg.sql.Identifier(self._table_cases_name)),
                (
                    name,
                    index,
                    round_type,
                    seed,
                    seed_index,
                    get_time_stamp()
                )
            ]
        )
        self._current_test_case_index = index

    def open_test_step(self, description):
        self._queue.append(
            [
                psycopg.sql.SQL(
                    """INSERT INTO {} (test_case_index, type, description, data, is_truncated, timestamp)
                       VALUES(%s, %s, %s, %s, %s, %s)"""
                ).format(psycopg.sql.Identifier(self._table_steps_name)),
                (
                    self._current_test_case_index,
                    "step",
                    description,
                    b"",
                    False,
                    get_time_stamp()
                )
            ]
        )

    def log_check(self, description):
        self._queue.append(
            [
                psycopg.sql.SQL(
                    """INSERT INTO {} (test_case_index, type, description, data, is_truncated, timestamp)
                       VALUES(%s, %s, %s, %s, %s, %s)"""
                ).format(psycopg.sql.Identifier(self._table_steps_name)),
                (
                    self._current_test_case_index,
                    "check",
                    description,
                    b"",
                    False,
                    get_time_stamp()
                )
            ]
        )

    def log_error(self, description):
        self._queue.append(
            [
                psycopg.sql.SQL(
                    """INSERT INTO {} (test_case_index, type, description, data, is_truncated, timestamp)
                       VALUES(%s, %s, %s, %s, %s, %s)"""
                ).format(psycopg.sql.Identifier(self._table_steps_name)),
                (
                    self._current_test_case_index,
                    "error",
                    description,
                    b"",
                    False,
                    get_time_stamp()
                )
            ]
        )
        self._problem_detected = True
        self._write_log()

    def log_recv(self, data):
        self._queue.append(
            [
                psycopg.sql.SQL(
                    """INSERT INTO {} (test_case_index, type, description, data, is_truncated, timestamp)
                       VALUES(%s, %s, %s, %s, %s, %s)"""
                ).format(psycopg.sql.Identifier(self._table_steps_name)),
                [
                    self._current_test_case_index,
                    "receive",
                    "",
                    memoryview(data),
                    False,
                    get_time_stamp()
                ]  # List and not tuple because it might trunc the data
            ]
        )

    def log_send(self, data):
        self._queue.append(
            [
                psycopg.sql.SQL(
                    """INSERT INTO {} (test_case_index, type, description, data, is_truncated, timestamp)
                       VALUES(%s, %s, %s, %s, %s, %s)"""
                ).format(psycopg.sql.Identifier(self._table_steps_name)),
                [
                    self._current_test_case_index,
                    "send",
                    "",
                    memoryview(data),
                    False,
                    get_time_stamp()
                ]  # List and not tuple because it might trunc the data
            ]
        )

    def log_info(self, description):
        self._queue.append(
            [
                psycopg.sql.SQL(
                    """INSERT INTO {} (test_case_index, type, description, data, is_truncated, timestamp)
                       VALUES(%s, %s, %s, %s, %s, %s)"""
                ).format(psycopg.sql.Identifier(self._table_steps_name)),
                (
                    self._current_test_case_index,
                    "info",
                    description,
                    b"",
                    False,
                    get_time_stamp()
                )
            ]
        )

    def log_fail(self, description=""):
        self._queue.append(
            [
                psycopg.sql.SQL(
                    """INSERT INTO {} (test_case_index, type, description, data, is_truncated, timestamp)
                       VALUES(%s, %s, %s, %s, %s, %s)"""
                ).format(psycopg.sql.Identifier(self._table_steps_name)),
                (
                    self._current_test_case_index,
                    "fail",
                    description,
                    b"",
                    False,
                    get_time_stamp()
                )
            ]
        )
        self._problem_detected = True

    def log_target_warn(self, description=""):
        self._queue.append(
            [
                psycopg.sql.SQL(
                    """INSERT INTO {} (test_case_index, type, description, data, is_truncated, timestamp)
                       VALUES(%s, %s, %s, %s, %s, %s)"""
                ).format(psycopg.sql.Identifier(self._table_steps_name)),
                (
                    self._current_test_case_index,
                    "target-warn",
                    description,
                    b"",
                    False,
                    get_time_stamp()
                )
            ]
        )
        self._problem_detected = True

    def log_target_error(self, description=""):
        self._queue.append(
            [
                psycopg.sql.SQL(
                    """INSERT INTO {} (test_case_index, type, description, data, is_truncated, timestamp)
                       VALUES(%s, %s, %s, %s, %s, %s)"""
                ).format(psycopg.sql.Identifier(self._table_steps_name)),
                (
                    self._current_test_case_index,
                    "target-error",
                    description,
                    b"",
                    False,
                    get_time_stamp()
                )
            ]
        )
        self._problem_detected = True

    def log_pass(self, description=""):
        self._queue.append(
            [
                psycopg.sql.SQL(
                    """INSERT INTO {} (test_case_index, type, description, data, is_truncated, timestamp)
                       VALUES(%s, %s, %s, %s, %s, %s)"""
                ).format(psycopg.sql.Identifier(self._table_steps_name)),
                (
                    self._current_test_case_index,
                    "pass",
                    description,
                    b"",
                    False,
                    get_time_stamp()
                )
            ]
        )

    def close_test_case(self):
        self._write_log(force=False)

    def close_test(self):
        self._write_log(force=True)

    def _write_log(self, force=False):
        if len(self._queue) > 0:
            if self._queue_max_len > 0:
                while (
                        self._current_test_case_index - next(x for x in self._queue[0] if isinstance(x, int))
                ) >= self._queue_max_len:
                    self._queue.popleft()
            else:
                force = True

            if force or self._problem_detected or self._log_first_case:
                for query in self._queue:
                    # abbreviate long entries first
                    if not self._problem_detected:
                        self._truncate_send_recv(query)
                    self._db_cursor.execute(query[0], query[1])
                self._queue.clear()
                self._db_connection.commit()
                self._log_first_case = False
                self._problem_detected = False

    def _truncate_send_recv(self, query):
        if query[1][1] in ["send", "recv"] and len(query[1][3]) > self._data_truncate_length:
            query[1][4] = True
            query[1][3] = memoryview(query[1][3][: self._data_truncate_length])


class FuzzLoggerPostgresReader:
    """Read fuzz data saved using FuzzLoggerPostgres

    Args:
        db_table_name (str): Name of table in database.
    """

    def __init__(self, db_name: str, db_table_name: str | None = None):
        verify_name_len(db_name, db_table_name)

        abs_db_socket_path = get_db_socket_path()

        self._db_connection = psycopg.connect(
            host=abs_db_socket_path,
            dbname=db_name,
            user=boofuzz.constants.DB_USER_NAME,
            password=boofuzz.constants.DB_PASSWORD
        )
        self._db_cursor = self._db_connection.cursor()

        self._db_cursor.execute("SET timezone = 'UTC'")
        self._db_connection.commit()

        self._table_cases_name = 'cases' if db_table_name is None else db_table_name + '_cases'
        self._table_steps_name = 'steps' if db_table_name is None else db_table_name + '_steps'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._db_cursor.close()
        self._db_connection.close()

    def get_test_case_data(self, index: int) -> data_test_case.DataTestCase:
        return _get_test_case_data(self._db_connection, self._table_cases_name, self._table_steps_name, index)

    def get_data_for_continue_command(self) -> (str, int, int):
        self._db_cursor.execute(
            psycopg.sql.SQL(
                """SELECT round_type, seed_index FROM {} ORDER BY number DESC LIMIT 1"""
            ).format(psycopg.sql.Identifier(self._table_cases_name))
        )

        round_type, seed_index = self._db_cursor.fetchone()

        self._db_cursor.execute(
            psycopg.sql.SQL(
                """SELECT number FROM {} WHERE round_type = %s AND seed_index = %s ORDER BY number ASC LIMIT 1"""
            ).format(psycopg.sql.Identifier(self._table_cases_name)),
            (
                round_type,
                seed_index
            )
        )

        mutant_index = self._db_cursor.fetchone()[0]  # First mutant_index with this round_type and seed_index

        return round_type, seed_index, mutant_index

    def get_total_mutant_index(self) -> int:
        self._db_cursor.execute(
            psycopg.sql.SQL(
                """SELECT number FROM {} ORDER BY number DESC LIMIT 1"""
            ).format(psycopg.sql.Identifier(self._table_cases_name))
        )
        total_mutant_index = self._db_cursor.fetchone()[0]

        return total_mutant_index

    def get_datname_and_db_size(self) -> Generator[tuple[str, str], None, None]:
        """Return a generator of tuple which contains every database name : (db_name, db_size)"""
        self._db_cursor.execute(
            """
            SELECT datname,
                pg_size_pretty(pg_database_size(datname)) as db_size
            FROM pg_database
            WHERE datistemplate = false
                AND datname NOT IN ('fuzz', 'postgres')
            ORDER BY datname;
            """
        )
        while (res := self._db_cursor.fetchone()) is not None:
            yield res

    @staticmethod
    def open_cli_connection(db_name: str = None):
        """This function open a Postgres shell with psql"""
        if db_name is None:
            db_name = boofuzz.constants.DB_DEFAULT_NAME

        verify_name_len(db_name, None)

        abs_db_socket_path = get_db_socket_path()

        print(f'The psql shell will open, use {Fore.BLUE}ctrl+d{Style.RESET_ALL} or '
              f'{Fore.BLUE}\\q{Style.RESET_ALL} to quit.\n')

        subprocess.run(['psql',
                        f'--host={abs_db_socket_path}',
                        f'--username={boofuzz.constants.DB_USER_NAME}',
                        f'--dbname={db_name}'])

    # def query(self, query, params=None):
    #     if params is None:
    #         params = []
    #     c = self._db_cursor
    #     return c.execute(query, params)
    #
    @property
    def failure_map(self):
        self._db_cursor.execute(
            psycopg.sql.SQL(
                '''SELECT test_case_index, description FROM {} WHERE type=%s '''
            ).format(psycopg.sql.Identifier(self._table_steps_name)),
            (
                'fail',
            )
        )
        failure_steps = self._db_cursor.fetchall()

        failure_map = collections.defaultdict(list)
        for step in failure_steps:
            failure_map[step[0]].append(step[1])
        return failure_map
