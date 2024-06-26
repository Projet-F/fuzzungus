#!/bin/bash

# UTILS
## Function to display help
function display_help() {
    echo "Usage: $0 [option...]
    
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
    
    /!\ Warning : UDP communication is not reliable. Use SSH for a more reliable communication."
}

## Log function to print to cli according to verbose mode
log() {
    local level="$1"
    local data="$2"
    if [[ $level -le $verbose ]]; then
        echo "$data"
    fi
}

## Escaping json characters
json_escape() {
    local input_string escaped_string

    input_string="$1"

    # Escape characters according to the specified rules
    escaped_string=$(echo "$input_string" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\t/\\t/g' -e 's/\n/\\n/g' -e 's/\r/\\r/g' -e 's/\x08/\\b/g' -e 's/\x0C/\\f/g')

    echo "$escaped_string"
}

# Print help if no arguments are provided
if [ $# -eq 0 ]; then
    display_help
    exit 0
fi

# Array of commands to check
commands=("ls" "cat" "grep" "awk" "basename" "read" "nc" "getopt")

# Initialize command existence variables
is_ls=false
is_cat=false
is_grep=false
is_awk=false
is_basename=false
is_read=false
is_nc=false
is_getopt=false

# Check that each command exists
# TODO: Check for command existance before calling functions
for cmd in "${commands[@]}"; do
    if command -v "$cmd" &> /dev/null; then
        declare "is_$cmd"=true
        log 1 "  [+]  Command '$cmd' found."
    else
        log 0 "  [-] Warning: Required command '$cmd' not found. Some data won't be parsed." >&2
    fi
done

# Constances 
maxverbose=2
regex_decimal_number='^[0-9]+(\.[0-9]+)?$'

# Set variables
#pid="0"
cpu=false
sys=false
mem=false
up=false
names=""
verbose=0
timeout=0
debug=false
ip=127.0.0.1
port=65431
udp=false
ssh=false
rounds=-1

# Parse command-line options
OPTIONS=$(getopt -o n:t:i:p:r:dcsmuavh --long names:,rounds:timeout:,ip:,port:,udp,ssh,debug,cpu,sys,mem,up,all,verbose,help -- "$@")

eval set -- "$OPTIONS"

while true; do
    case "$1" in
        -h | --help )
            display_help
            exit ;;
        -a | --all )
            cpu=true
            sys=true
            mem=true
            up=true
            shift ;;
        -c | --cpu )
            cpu=true
            shift ;;
        -s | --sys )
            sys=true
            shift ;;
        -m | --mem )
            mem=true
            shift ;;
        -u | --up )
            up=true
            shift ;;
        -n | --names )
            names=$2
            # Remove the leading and trailing brackets
            names="${names#[}"
            names="${names%]}"
            # Remove the quotes around the names
            names="${names//\"}"
            names="${names//\'}"
            IFS=', ' read -r -a names_array <<< "$names"
            shift 2 ;;
        -v | --verbose )
            ((verbose+=1))
            shift ;;
        -t | --timeout )
            timeout=$2
            if ! [[ $timeout =~ ^[0-9]+$ ]]; then
                echo "Error: Usage: -t|--timeout <number>" >&2; exit 1
            fi
            shift 2 ;;
        -r | --rounds )
            rounds=$2
            if ! [[ $rounds =~ ^[0-9]+$ ]]; then
                echo "Error: Usage: -r|--rounds <number>" >&2; exit 1
            fi
            shift 2 ;;
        -i | --ip )
            ip=$2
            if ! [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
                echo "Error: Usage: -i|--ip <1.2.3.4>" >&2; exit 1
            fi
            shift 2 ;;
        -p | --port )
            port=$2
            if ! [[ $port =~ ^[0-9]{1,5}$ ]]; then
                echo "Error: Usage: -p|--port <port_number>" >&2; exit 1
            fi
            shift 2 ;;
        -d | --debug )
            debug=true
            shift ;;
        --ssh )
            ssh=true
            shift ;;
        --udp )
            udp=true
            shift ;;
        -- )
            shift
            break ;;
        * )
            echo "Error: Internal error!" >&2
            exit 1 ;;
  esac
done

# Starting procmon
log 1 "Starting procmon..."

# Check for -t or -d
if [ "$timeout" -ne 0 ] && [ $debug = true ]; then
    log 0 "[-] Error: Can't have -t and -d"
    exit
fi

# Check for --ssh or --udp
if [ $ssh = true ] && [ $udp = true ]; then
    log 0 "[-] Error: Can't have --udp and --ssh"
    exit
fi


# Max verbose
if [ $verbose -ge $maxverbose ] ; then
    verbose=$maxverbose
fi

# PID
## Function to get list of PIDs
get_list_of_pids() {
    # Read only folders that have integer name
    # Each number represents the PID of a running process
    pid_folders=$(ls /proc/ | grep -E '^[0-9]+$')

    # Print each PID
    for pid in $pid_folders; do
        echo "$pid"
    done
}

## Get PID list that matches the name
get_pid_list_by_name() {
    name="$1"

    local -n pid_array=$2

    for pid_dir in /proc/[0-9]*; do
        # Extract the PID from the directory path
        pid=$(basename "$pid_dir")

        # Check if the PID is a directory
        if [ -d "$pid_dir" ]; then
            # Check if the comm file exists
            if [ -f "$pid_dir/comm" ]; then
                # Read the command from the comm file
                read_buffer=$(cat "$pid_dir/comm")

                # Check if the command matches the provided process name
                if [[ "$read_buffer" == *"$name"* ]]; then
                    # Add the PID to the list of matching PIDs
                    pid_array+=("$pid")
                fi
            fi
        fi
    done
}

## Function to get CPU usage and uptime for a PID
get_pid_cpu_and_uptime() {
    local pid u_time s_time cu_time cs_time start_time total_time hz up_time cpu
    # Check if PID is provided
    pid=$1

    # Check if the process exists
    if [ ! -d "/proc/$pid" ]; then
        echo ""
        return 1
    fi

    # Read the stat file
    read -r -a stats <<< "$(cat /proc/"$pid"/stat)"

    # Extract the necessary fields
    u_time=${stats[13]}
    s_time=${stats[14]}
    cu_time=${stats[15]}
    cs_time=${stats[16]}
    start_time=${stats[21]}

    # Calculate total time
    total_time=$((u_time + s_time + cu_time + cs_time))

    # Get clock ticks per second
    hz=$(getconf CLK_TCK)

    # Get system uptime
    up_time=$(cat /proc/uptime | awk '{print $1}')

    # Calculate process uptime and CPU usage
    uptime=$(awk "BEGIN {print $up_time - $start_time / $hz}")
    cpu=$(awk "BEGIN {print 100 * ($total_time / $hz) / $uptime}")

    # Print the result
    echo "$cpu $uptime"
}

## Function to get memory usage for a PID
get_pid_mem() {
    local pid data stack rss size total_mem total_ram total_size
    pid=$1

    # Check if the process exists
    if [ ! -e "/proc/$pid/status" ]; then
        echo "Process got terminated"
        return 1
    fi

    # Read the status file
    while read -r line; do
        case $line in
            VmData:*)
                data=${line#VmData:}
                data=${data%% kB*}
                ;;
            VmStk:*)
                stack=${line#VmStk:}
                stack=${stack%% kB*}
                ;;
            VmRSS:*)
                rss=${line#VmRSS:}
                rss=${rss%% kB*}
                ;;
            VmSize:*)
                size=${line#VmSize:}
                size=${size%% kB*}
                ;;
        esac
    done < "/proc/$pid/status"

    # Calculate total memory
    total_mem=$((data + stack))
    total_ram=$((rss))
    total_size=$((size))

    # Print the result
    echo "$total_mem $total_ram $total_size"
}

## Function to get command line that started the process
get_pid_command_line() {
    local pid file_name process_cli
    pid=$1
    file_name="/proc/$pid/cmdline"

    if [ ! -f "$file_name" ]; then
        echo "process got terminated"
        return 1
    fi

    # Read the command line and remove the null character
    process_cli=$(tr -d '\0' < "$file_name")
    echo "$process_cli"
}

## Function to get process name
get_pid_process_name() {
    local pid file_name process_name
    pid=$1
    file_name="/proc/$pid/comm"

    if [ ! -f "$file_name" ]; then
        echo "process got terminated"
        return 1
    fi

    process_name=$(cat "$file_name")
    echo "$process_name"
}

# SYSTEM INFOS
# Steps:
#   Read the file /proc/cpuinfo till you find the line with “cpu cores” in string.
#   Split the line based on white space.
#    The last element of the array will be number of cores.
#    Multiply it by 2 to get the number of procs.

get_system_infos() {
    # Get the number of CPUs
    local cpu_core_count cpu_count total_mem total_swap kernel_version
    cpu_core_count=$(cat /proc/cpuinfo | awk '/cpu cores/ {print $NF}' | uniq)
    #cpu_count=$((cpu_core_count/2))

    # Get the total memory
    total_mem=$(grep MemTotal /proc/meminfo | awk '{print $2}')

    # Get the total swap
    total_swap=$(grep SwapTotal /proc/meminfo | awk '{print $2}')

    # Get the kernel version
    kernel_version=$(uname -r)
    echo "$cpu_core_count $total_mem $total_swap $kernel_version"


}

# CPU USAGE
# Steps:
#   Read the first line of /proc/stat.
#   Discard the first word which is always cpu.
#   Add all of the values in the line to get the total time.
#   Take difference of change in total time and idle time at 1 second interval.
#   Divide the idle time( fourth value) by total time to get fraction of idle time
#   Subtract 1 with the idle time to get percentage of non idle time.
#   Multiple by 100 to get a current cpu percentage.

## Function to read CPU file
read_cpu_file() {
    # Extracting the fourth column ("idle") from /proc/stat
    local idle_time total_time
    idle_time=$(grep 'cpu ' /proc/stat | awk '{print $5}')
    # Extracting the total time from /proc/stat
    total_time=$(grep 'cpu ' /proc/stat | awk '{print $2+$3+$4+$5+$6+$7+$8}')
    echo "$idle_time $total_time"
}

# Function to calculate CPU usage
calculate_cpu() {
    local last_idle last_total current_idle current_total del_idle del_total cpu_usage
    read -r last_idle last_total <<< "$1"
    read -r current_idle current_total <<< "$2"
    
    # Calculating the difference in idle and total times
    del_idle=$((current_idle - last_idle))
    del_total=$((current_total - last_total))
    
    # Calculating CPU usage percentage
    cpu_usage=$(awk "BEGIN {print (1 - $del_idle / $del_total) * 100}")
    echo "$cpu_usage"
}

# Function to get current CPU usage
get_current_cpu() {
    last_stats=$(read_cpu_file)
    sleep 1
    current_stats=$(read_cpu_file)
    cpu_usage=$(calculate_cpu "$last_stats" "$current_stats")
    echo "$cpu_usage"
}

# MEMORY USAGE
# Steps :
#   Read the /proc/meminfo file.
#   Find all the parameters : MemTotal, MemFree, Buffers, Cached, SwapCached, SwapTotal, SwapFree, Shmem, SReclaimable
#   Do calculation
## Function to extract parameter from /proc/meminfo
extract_parameter() {
    parameter=$1
    value=$(grep "^$parameter" /proc/meminfo | awk '{print $2}')
    echo "$value"
}

## Function to calculate memory values
calculate_memory_values() {
    MemTotal=$(extract_parameter "MemTotal:")
    MemFree=$(extract_parameter "MemFree:")
    Buffers=$(extract_parameter "Buffers:")
    Cached=$(extract_parameter "Cached:")
    SwapTotal=$(extract_parameter "SwapTotal:")
    SwapFree=$(extract_parameter "SwapFree:")
    shared=$(extract_parameter "Shmem:")
    Slab=$(extract_parameter "SReclaimable:")

    # Calculating used, free, and buff/cache values
    used=$((MemTotal - MemFree - Buffers - Cached - Slab))
    free=$MemFree
    buff_cache=$((Buffers + Cached + Slab))

    # Extracting MemAvailable and shared values
    MemAvailable=$(extract_parameter "MemAvailable:")

    # Calculating Swap values
    SwapUsed=$((SwapTotal - SwapFree))

    # Outputting the calculated values
    echo $MemTotal $used $free $MemAvailable $shared $buff_cache $SwapTotal $SwapUsed $SwapFree
}

# UPTIME
read_uptime() {
    uptime_info=$(head -n1 /proc/uptime)
    uptime_seconds=$(echo "$uptime_info" | awk '{print $1}')
    echo "$uptime_seconds"
}

# MAIN
main() {
    local escaped_value system_vars process_vars json count

    system_vars=(cpu_core_count total_mem total_swap kernel_version system_cpu system_uptime system_mem_total system_mem_used system_mem_free system_mem_available system_mem_shared system_mem_buff_cache system_swap_total system_swap_used system_swap_free)
    process_vars=(process_cpu process_uptime process_mem process_command_line process_ram process_vmem)

    # Start the JSON string
    json="{"

    count=1

    # While loop to do the following:
    while [ $count -le "$rounds" ] || [ "$rounds" -eq -1 ]
    do
        log 1 "[+] Round $count"

        # Start Json
        json="{"

        # Get system infos
        if [ $sys == "true" ] ; then
            read -r cpu_core_count total_mem total_swap kernel_version  <<< "$(get_system_infos)"
        fi
        # Get cpu infos
        if [ "$cpu" == "true" ]; then
            read -r system_cpu <<< "$(get_current_cpu)"
        fi
        # Get uptime infos
        if [ $up == "true" ]; then
            read -r system_uptime <<< "$(read_uptime)"
        fi
        # Get memory infos
        if [ $mem == "true" ]; then
            read -r system_mem_total system_mem_used system_mem_free system_mem_available system_mem_shared system_mem_buff_cache system_swap_total system_swap_used system_swap_free <<< "$(calculate_memory_values)"
        fi

        log 1 "  [+] Getting system infos"

        # Loop over the variable names
        for var in "${system_vars[@]}"; do
            # Get the value of the variable
            value=${!var}
            # Check if the value is a number
            if [[ $value =~ $regex_decimal_number ]]; then
                # If it's a number, add it to the JSON string without quotes
                json+="\"$var\": $value,"
            else
                # If it's not a number, add it to the JSON string with quotes
                read -r escaped_value <<< "$(json_escape "$value")"
                json+="\"$var\": \"$escaped_value\","
            fi
        done

        # Loop over process names
        for name in "${names_array[@]}"; do
            log 1 "  [+] Getting process $name infos"
            local pids=()
            get_pid_list_by_name "$name" pids
            # Add a subsection to json for each process
            json+="\"$name\":{"
            # Loop over PIDs
            for pid in "${pids[@]}"; do
                log 1 "      [+] Getting PID $pid infos for process"
                if [ "$pid" -ne 0 ]; then
                    read -r process_cpu process_uptime <<< "$(get_pid_cpu_and_uptime "$pid")"
                    read -r process_mem process_ram process_vmem <<< "$(get_pid_mem "$pid")"
                    read -r process_command_line <<< "$(get_pid_command_line "$pid")"
                    # read -r process_name <<< "$(get_pid_process_name "$pid")"
                fi
                # Add a subsection to json for each PID
                json+="\"$pid\":{"
                for var in "${process_vars[@]}"; do
                    value=${!var}
                    if [[ $value =~ $regex_decimal_number ]]; then
                        json+="\"$var\": $value,"
                    else
                        read -r escaped_value <<< "$(json_escape "$value")"
                        json+="\"$var\": \"$escaped_value\","
                    fi
                done
                # Remove the trailing , and replace it by },
                json="${json%,}},"
            done
            # Remove the trailing , and replace it by },
            json="${json%,}},"
        done

        # Remove the trailing comma and close the JSON string
        json="${json%,}}"

        log 1 "  [+] Sending to $ip:$port"

        if [ $udp = true ]; then
            echo -n "$json" | nc -u -w1 "$ip" "$port"
        else
            echo  "$json"
        fi
        #echo -n "$json" | nc -u -w0 "127.0.0.1" "65431"

        log 2 "$json"

        log 2 "  [+] Data size : ${#json}"

        count=$((count+1))

        # Wait between rounds
        if [ "$timeout" -ne 0 ]; then
            log 1 "[+] Sleeping $timeout seconds"
            sleep "$timeout"
        elif [ "$debug" = true ]; then
            log 1 "[+] Waiting for input..."
            read -r -n 1
        fi

    done
}

main
