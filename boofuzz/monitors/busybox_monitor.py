"""Simple monitor for a busybox machine, using an external procmon script written in bash."""
import subprocess
import json

from boofuzz.loggers import FuzzLogger

from .base_monitor import BaseMonitor

def format_bytes(size):
    """
    Function to format the size of a file in bytes, kilobytes, megabytes, gigabytes or terabytes.

    :type size: int
    :param size: Size of the file in bytes

    :return: str
    """
    # 2**10 = 1024
    power = 2**10
    n = 1
    power_labels = {1: 'kilo', 2: 'mega', 3: 'giga', 4: 'tera'}
    while size > power:
        size /= power
        n += 1
    return str(size) + power_labels[n]+'bytes'


class BusyboxMonitor(BaseMonitor):
    """
    This Class aims to implement the python side of an external monitor written in bash,
    designed for a simple machine like a busybox.
    It is able to communicate in SSH.

    The data sent by the procmon is a JSON, with the following structure :

    .. code-block:: json

        {
            "cpu_count": 8,
            "total_mem": 16054272,
            "total_swap": 999420,
            "kernel_version": "6.1.0-21-amd64",
            "system_cpu": "0.581154",
            "system_uptime": "9157.06",
            "system_mem_total": 16054272,
            "system_mem_used": 4894352,
            "system_mem_free": 6958548,
            "system_mem_available": 9385460,
            "system_mem_shared": 1431144,
            "system_mem_buff_cache": 4201372,
            "system_swap_total": 999420,
            "system_swap_used": 0,
            "system_swap_free": 999420,
            "firefox": {
                "2993": {
                    "process_cpu": "5.22458112198275910876",
                    "process_uptime": "8831.33000000000000000000",
                    "process_mem": 1314008,
                    "process_command_line": "/usr/lib/firefox-esr/firefox-esr",
                    "process_ram": 590748,
                    "process_vmem": 4722748
                }
            }
        }

    With a section for each process to monitor, and a subsection for each PID of the process.

    If you want to test manually your SSH connection to debug something,
    the command should look something like this :

    .. code-block:: bash
    
        sshpass -p $password ssh $username@$ip "<procmon_path> --ssh -a -n '['$process_name']' -r 1"

    Or any other options according to `procmon.sh -h` : 

    .. code-block:: bash

        Usage: ./monitors/procmon.sh [option...]
            
            Data to monitor
            ===============
                -c, --cpu                   Display CPU information
                -s, --sys                   Display system information
                -m, --mem                   Display memory information
                -u, --up                    Display system uptime
                -a, --all                   Display all information. PID or Name required
            
            Execution options to monitor
            ============================
                -h, --help                  Display help
                -n, --names <name>          Find processes by name
                -t, --timeout <timeout>     Timeout between rounds
                -r, --rounds                Number of rounds to execute. Infinite by default.
                -v, --verbose               Verbose
                -d, --debug                 Debug mode, wait for user input between rounds
            
            Network options
            ===============
                -i, --ip <ip>               IP address to send the data to. Localhost by default
                -p, --port <port>           Port to send the data to. 65431 by default
                --udp                       Send data via UDP
                --ssh                       Send data via SSH

            /!\\ Warning : UDP communication is not reliable. Use SSH for a more reliable communication
    
    As you can read above, the UDP communication was the initial communication method,
    but it is not reliable. You have to parse multiple JSON at once in your buffer,
    you don't have a lot of feedback, and you can't communication with the script,
    even just to close it.

    For now the communication is done via SSH, which is more reliable, but slower.
    We open a SSH connection, send the command, read the output, and close the connection.
    That way we are sure to have the entire output, and we can communicate with the script to give
    new commands on another round if necessary. And it closes itself after sending its data.

    Also note that the errors at connection (timeout, rights...) are printed to the console,
    so don't hesitate to execute by hand the SSH command to debug the connection.

    Room for improvement :
    The busybox monitor currently doesn't uses all the information given by the procmon script.

    For crash detection, it uses :

    - The PIDs of the processes to detect if a PID changed
    - `process_uptime` to get the uptime of the processes and detect crashes

    For abnormal behaviour detection, it uses :

    - `system_cpu` and `cpu_core_count` to get the CPU usage of the system
    - `system_mem_used` and `system_mem_total` to get the memory usage of the system
    - `process_cpu` and `process_mem` to get the CPU and memory usage of the processes

    It could use :

    - `system_mem_shared`, `system_mem_buff_cache`, `system_swap_total`, `system_swap_used`, `system_swap_free` to get more information about the memory usage of the system
    - `process_command_line`, `process_ram`, `process_vmem` to get more information about the processes

    :type target_ip: str
    :param target_ip: IP of the target
    :type target_port: int
    :param target_port: Port of the target
    :type target_user: str
    :param target_user: User of the target to connect to SSH
    :type target_password: str
    :param target_password: Password of the target. For SSH connections only. 
        If passed, sshpass is used if present. 
        Otherwise, only ssh is used, allowing the use of ssh keys if they are configured.
    :type processes_to_monitor: list[str]
    :param processes_to_monitor: List of processes to monitor
    :type procmon_path: str
    :param procmon_path: Path to the procmon script on the target
    """

    # Array of words that indicate an error in the output
    error_array = [
        "error",
        "fail",
        "permission denied",
        "No route to host",
        "Connection refused",
        "invalid",
        "not found",
        "not exist",
        "no such",
        "denied",
        "failed",
        "unable",
        "timeout",
        "unreachable",
        "unavailable",
        "unauthorized",
        "not allowed",
        "not permitted",
        "not supported",
        "rejected",
        "not valid",
        "not correct",
        "not working",
        "not running",
        "not started",
        "not stopped",
        "not connected",
        "not found",
        "not available",
        "not reachable"]

    def __init__(self, target_ip: str, target_port: int,
                 processes_to_monitor: list[str], procmon_path: str,
                 cpu_percentage_threshold: int = 80, mem_percentage_threshold: int = 80,
                 target_user: str = "", target_password: str = "",
                 ssh_command_timeout: int = 2
                 ):
        super().__init__()
        # Generic connections parameters
        self.target_ip = target_ip
        self.target_port = target_port
        self.processes_to_monitor = processes_to_monitor
        self.procmon_path = procmon_path

        # Specific parameters for SSH connections
        self.target_user = target_user
        self.target_password = target_password
        self.ssh_command_timeout = ssh_command_timeout

        # Specific parameters for abnormal behaviour detection
        self.cpu_percentage_threshold = cpu_percentage_threshold
        self.mem_percentage_threshold = mem_percentage_threshold

        # Check that target_user and target_password are set to start procmon via SSH
        if not self.target_user or not self.target_password:
            raise ValueError(
                "target_user and target_password are required when connection_type is 'ssh'")

        # Check if sshpass is installed
        try:
            subprocess.run(["which", "sshpass"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.is_sshpass = True
        except subprocess.CalledProcessError:
            # TODO : maybe link the logger to the object ?
            print("Warning: sshpass is not installed on the machine. Using ssh instead.")
            self.is_sshpass = False

        # Process object to store the process started by the monitor
        self.process: subprocess.Popen | None = None
        self.stdout: str = ""
        self.stderr: str = ""

        # Data of the last round
        self.last_data: str = None

        # Synopsis of the last crash
        self.last_crash_synopsis: str = ""

    def alive(self, fuzz_data_logger: FuzzLogger = None) -> bool:
        """
        Check if the target is still alive.
        """

        if self.process is not None and self.process.poll() is None:
            return True
        return self.start_target(fuzz_data_logger)

    def post_send(self, target=None, fuzz_data_logger: FuzzLogger = None, session=None) -> bool:
        """
        Called after the current fuzz node is transmitted. Use it to collect
        data about a target and decide whether it crashed.

        If UDP, calls alive() to check if the target is still alive. If SSH, restarts the procmon.

        returns: Bool. True if the target is still alive, False if it crashed.
        """

        # Restart the target
        if self.start_target(fuzz_data_logger):
            return self.post_start_target(target, fuzz_data_logger, session)
        else:
            self.last_crash_synopsis = "Error starting the target"
        return False

    def start_target(self, fuzz_data_logger: FuzzLogger = None, *args, **kwargs) -> bool:
        """
        Starts the procmon script :
        - If UDP, sends the command via SSH and creates a socket to receive the data that is sent continuously
        - If SSH, sends the command via SSH, reads the output in STDOUT, and closes the connection to assure that the entire output is read

        returns: Bool. True if the target started successfully, False if there was an error.
        """
        # Get the ssh part of the command

        ssh_command = f'ssh -o StrictHostKeyChecking=no {self.target_user}@{self.target_ip} "{self.procmon_path} -a -n \'{self.processes_to_monitor}\' --ssh -r 1"'

        # Get the sshpass part of the command
        if self.is_sshpass:
            command = f'sshpass -p {self.target_password} {ssh_command}'
        else:
            command = ssh_command

        try:
            # Execute the command and capture output
            self.process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            text=True)
            self.stdout, self.stderr = self.process.communicate(timeout=self.ssh_command_timeout)

            # If stdout contains words like "error" or "fail", print the error message
            for flux in [self.stdout, self.stderr]:
                if any(word in flux for word in self.error_array):
                    self.last_crash_synopsis = f"Error starting the target: {flux}"
                    fuzz_data_logger.log_fail(self.last_crash_synopsis)
                    self.stop_target()
                    return False
            return True
        except subprocess.CalledProcessError as e:
            # If there's an error, print the error message
            self.last_crash_synopsis = f"Error starting the target: {e}"
            fuzz_data_logger.log_fail(self.last_crash_synopsis)
            return False
        except subprocess.TimeoutExpired as e:
            self.last_crash_synopsis = f"Error starting the target: {e}"
            fuzz_data_logger.log_fail(self.last_crash_synopsis)
            return False

    def stop_target(self) -> bool:
        """
        Stops the procmon script :
        - If UDP, sends a SIGINT to the procmon script via self.process via SSH, and closes the socket
        - If SSH, closes the process that opened the SSH connection

        returns: True if the target stopped successfully, False if there was an error.
        """

        self.process.kill()
        self.process.wait()
        return True

    def restart_target(self, target=None, fuzz_data_logger=None, session=None):
        """
        Restarts the target. Tries to stop it, then start it again.
        """
        self.stop_target()
        return self.start_target(fuzz_data_logger)

    def post_start_target(self, target=None, fuzz_data_logger: FuzzLogger = None, session=None):
        """
        Called after a target is started or restarted.
        """
        is_crash = False
        data_decoded = ""

        # Read and print the output continuously
        data_decoded = self.stdout

        is_crash = self._analyze_data(data_decoded, fuzz_data_logger)

        # Close the process
        self.stop_target()

        # Store the data for the next round
        self.last_data = data_decoded

        return not is_crash

    def get_crash_synopsis(self) -> str:
        """
        Get a synopsis of the crash.

        Read self.last_crash_synopsis to get the crash synopsis.

        returns: str
        """
        return self.last_crash_synopsis

    def _check_if_process_exists(self, data: str) -> list[str]:
        """
        For each process in self.processes_to_monitor, check if it is in the data, and if it has at least one PID.

        returns: list of processes that don't exist or have no PID
        """

        # Parse the JSON data
        data_dict: dict = json.loads(data)

        # Array to store the processes that don't exist or have no PID
        processes_not_found: list[str] = []

        # For each process to monitor
        for process in self.processes_to_monitor:
            # If the process is not in the data, it means it doesn't exist
            if process not in data_dict.keys():
                processes_not_found.append(process)
                continue
            # If the process is in the data, but has no PID, it means it doesn't exist
            if len(data_dict[process].keys()) == 0:
                # Append if it isn't already in the list
                if process not in processes_not_found:
                    processes_not_found.append(process)

        return processes_not_found

    def _analyze_data(self, data_decoded: str, fuzz_data_logger: FuzzLogger = None) -> bool:
        """
        Analyze the data (crash analysis and abnormal behaviour analysis)
        """

        # Check if the processes to monitor exist and have at least one PID
        processes_not_found = self._check_if_process_exists(data_decoded)
        if len(processes_not_found) > 0:
            self.last_crash_synopsis = f"The following processes don't exist or have no PID : {processes_not_found}"
            fuzz_data_logger.log_fail(self.last_crash_synopsis)
            return True

        is_crash = False

        # If the last_data is empty, it is the first round, so we don't analyze the data
        if self.last_data is not None:
            # Analyze the data (crash analysis and abnormal behaviour analysis)
            is_crash = self._crash_analysis(data_decoded, fuzz_data_logger)
            self._abnormal_behaviour_analysis(data_decoded, fuzz_data_logger)
        return is_crash

    def _crash_analysis(self, data: str, fuzz_data_logger: FuzzLogger = None) -> bool:
        """ 
        Parse the JSON data and look for two things :
        - Did a PID change ?
        - Is the uptime of a PID lower than it was before ? 
        """

        # Parse the JSON data and the last JSON data
        data_dict: dict = json.loads(data)
        last_data_dict: dict = json.loads(self.last_data)

        # For each process to monitor
        for process in self.processes_to_monitor:
            # Get the PID(s) of the process, for the actual and the last data
            current_pids = data_dict[process].keys()
            last_pids = last_data_dict[process].keys()

            # If last_pids is empty, it means the process didn't exist in the last round, so we can't compare the uptimes
            if len(last_pids) == 0:
                continue

            # If not all the PID of last_pids are in pids, it means a PID changed, and a crash occured
            if not all(pid in current_pids for pid in last_pids):
                self.last_crash_synopsis = f"A PID changed in the process {process}"
                fuzz_data_logger.log_fail(self.last_crash_synopsis)
                # Return here because if a PID changed, the comparaison of uptimes below could compare a PID that doesn't exist anymores
                return True

            # For each PID of the process, check if the uptime is lower than it was before
            for pid in current_pids:
                if float(data_dict[process][pid]['process_uptime']) < float(
                        last_data_dict[process][pid]['process_uptime']):
                    self.last_crash_synopsis = f"The process {process} with PID {pid} crashed (uptime detection)"
                    fuzz_data_logger.log_fail(self.last_crash_synopsis)
                    return True

        return False

    def _abnormal_behaviour_analysis(self, data: str, fuzz_data_logger: FuzzLogger = None) -> None:
        """
        Parse the JSON data and look for two things :
        - Is a process using too much CPU ?
        - Is a process using too much memory ?
        """

        # Parse the JSON data
        data_dict: dict = json.loads(data)

        # In general, check if the system is using too much CPU or memory, taking into account the number of CPU cores
        if float(data_dict['system_cpu']) > self.cpu_percentage_threshold / data_dict['cpu_core_count']:
            fuzz_data_logger.log_target_warn(
                f"The system is using too much CPU : {data_dict['system_cpu']}%, taking into account the number of CPU cores : {data_dict['cpu_core_count']}")
        if int(data_dict['system_mem_used']) > self.mem_percentage_threshold * data_dict['system_mem_total'] / 100:
            fuzz_data_logger.log_target_warn(
                f"The system is using too much memory : {data_dict['system_mem_used']} Kb")

        # For each process to monitor
        for process in self.processes_to_monitor:
            # For each PID of the process, check if the CPU usage, the memory usage, the ram, or the virtual memory is too high
            for pid in data_dict[process].keys():
                # CPU usage
                if float(data_dict[process][pid]['process_cpu']) > self.cpu_percentage_threshold:
                    fuzz_data_logger.log_target_warn(
                        f"The process {process} with PID {pid} is using too much CPU : {data_dict[process][pid]['process_cpu']}%")

                # Memory usage
                if int(data_dict[process][pid]['process_mem']) > self.mem_percentage_threshold * int(
                        data_dict['system_mem_total']) / 100:
                    fuzz_data_logger.log_target_warn(
                        f"The process {process} with PID {pid} is using too much memory : {format_bytes(data_dict[process][pid]['process_mem'])}")

                # RAM usage
                if int(data_dict[process][pid]['process_ram']) > self.mem_percentage_threshold * int(
                        data_dict['system_mem_total']) / 100:
                    fuzz_data_logger.log_target_warn(
                        f"The process {process} with PID {pid} is using too much RAM : {format_bytes(data_dict[process][pid]['process_ram'])}")

                # Virtual memory usage
                if int(data_dict[process][pid]['process_vmem']) > self.mem_percentage_threshold * int(
                        data_dict['system_mem_total']) / 100:
                    fuzz_data_logger.log_target_warn(
                        f"The process {process} with PID {pid} is using too much virtual memory : {format_bytes(data_dict[process][pid]['process_vmem'])}")
