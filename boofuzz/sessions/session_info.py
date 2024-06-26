import warnings

from ..loggers.fuzz_logger_postgres import FuzzLoggerPostgresReader


class SessionInfo:
    """
    .. versionchanged:: 0.4.2
       This class has been moved into the sessions' subpackage. The full path is now
       boofuzz.sessions.session_info.SessionInfo.
    """

    def __init__(self, db_name, db_table_name):
        self._db_reader = FuzzLoggerPostgresReader(db_name=db_name, db_table_name=db_table_name)

    @property
    def monitor_results(self):
        return self._db_reader.failure_map

    @property
    def monitor_data(self):
        return {-1, "Monitor Data is not currently saved in the database"}

    @property
    def procmon_results(self):
        warnings.warn(
            "procmon_results has been renamed to monitor_results."
            "This alias will stop working in a future version of boofuzz",
            FutureWarning,
        )
        return self.monitor_results

    @property
    def netmon_results(self):
        warnings.warn(
            "netmon_results is now part of monitor_data" "This alias will stop working in a future version of boofuzz",
            FutureWarning,
        )
        return self.monitor_data

    @property
    def fuzz_node(self):
        return None

    @property
    def total_num_mutations(self):
        return None

    @property
    def total_mutant_index(self):
        x = self._db_reader.get_total_mutant_index()
        return x

    @property
    def mutant_index(self):
        return None

    def test_case_data(self, index):
        """Return test case data object (for use by web server)

        Args:
            index (int): Test case index

        Returns:
            Test case data object
        """
        return self._db_reader.get_test_case_data(index=index)

    @property
    def is_paused(self):
        return False

    @property
    def state(self):
        return "finished"

    @property
    def exec_speed(self):
        return 0

    @property
    def runtime(self):
        return 0

    @property
    def current_test_case_name(self):
        return ""
