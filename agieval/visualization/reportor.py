import os
import sys
import socket
import subprocess
import time
import psutil
import urllib.parse

from agieval.common.logger import log, log_error, log_warn


DEFAULT_PORT = 38410

def is_port_in_use(port):
    """Check if port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_process_by_port(port):
    """Find process occupying specified port"""
    # Alternative method: use command line tool
    try:
        output = subprocess.check_output(f'lsof -i :{port} -n -P', shell=True).decode()
        if output:
            lines = output.strip().split('\n')
            if len(lines) > 1:  # Skip header line
                parts = lines[1].split()
                if len(parts) >= 2:
                    pid = int(parts[1])
                    return psutil.Process(pid)
    except (subprocess.SubprocessError, ValueError, psutil.NoSuchProcess, psutil.AccessDenied) as e:
        log_error(f"Error using lsof command to find process: {e}")
    return None

def is_reportor_server_running(port):
    """Check if our own server is running"""
    proc = find_process_by_port(port)
    if not proc:
        log_warn("No process found")
        return False, 0

    try:
        # Check if it's a Python process
        if 'python' not in proc.name().lower():
            log_warn("Checking if it's a Python process")
            return False, 0

        # Get full command line
        cmdline = proc.cmdline()
        # Check if it's http.server module
        if len(cmdline) >= 3 and cmdline[1] == '-m' and cmdline[2] == 'http.server':
            # Check if port number matches
            if len(cmdline) >= 4 and cmdline[3] == str(port):
                return True, proc.pid
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        pass

    return False, 0

def find_all_http_server_processes():
    """Find all http.server processes"""
    http_server_processes = []

    # Iterate through all processes
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if it's a Python process
            if 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                # Check if it's http.server module
                if len(cmdline) >= 3 and cmdline[1] == '-m' and cmdline[2] == 'http.server':
                    http_server_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Process may have ended or be inaccessible
            pass

    return http_server_processes

def start_background_server(port):
    """Start HTTP server in background"""
    # Build command to start server
    cmd = [sys.executable, "-m", "http.server", str(port), "--bind", "0.0.0.0"]
    log(f"Start command: {' '.join(cmd)}")

    # Start process in background
    with open(os.devnull, 'w') as devnull:
        subprocess.Popen(cmd, stdout=devnull, stderr=devnull,
                        start_new_session=True, close_fds=True)

    # Wait for server to start
    for _ in range(10):  # Wait up to 5 seconds
        if is_port_in_use(port):
            return True
        time.sleep(0.5)

    return False

def start_reportor(result_dir: str, port: int = DEFAULT_PORT):
    log("Starting evaluation report visualization service ...")
    path = os.path.join(os.getcwd(), result_dir)
    if not os.path.exists(path):
        log_error(f"Service startup exception, evaluation result directory {path} does not exist")
        return ""

    server_alive = False
    # Check if port is occupied
    if is_port_in_use(port):
        reportor_server_running, pid = is_reportor_server_running(port)
        if reportor_server_running:
            log(f"Server is already running on port {port}, process pid {pid}")
            server_alive = True
        else:
            log_warn(f"Error: Port {port} is occupied by another program")
    else:
        # Start server in background
        log(f"Starting server (port {port})...")
        if not start_background_server(port):
            log_error("Error: Unable to start server")
        else:
            server_alive = True
            log("Server started")
    # Build URL
    encoded_path = urllib.parse.quote(result_dir)
    url = f"http://localhost:{port}/agieval/visualization/reportor.html?path={encoded_path}"

    if not server_alive:
        return ""
    log("##################### Evaluation Report #####################")
    log(f"Visit the following URL to view the evaluation report: {url}")
    log("##################### Evaluation Report #####################")
    return url

def stop_reportor():
    """Stop all http.server services"""
    import subprocess
    import os

    # Use ps command to find all related http.server processes
    cmd = "ps -ef | grep \"http.server.*--bind 0.0.0.0\" | grep -v grep | awk '{print $2}'"
    try:
        # Execute command to get process ID list
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        pids = result.stdout.strip().split('\n')
        pids = [pid for pid in pids if pid]  # Filter empty strings

        if not pids:
            log("No running http.server service found")
            return []

        # Use kill -9 command to terminate all found processes
        killed_pids = []
        for pid in pids:
            try:
                os.system(f"kill -9 {pid}")
                killed_pids.append(str(pid))
            except Exception as e:
                log_error(f"Error terminating process {pid}: {e}")
        log(f"Terminated task process ID list: {', '.join(pids)}")
        return killed_pids
    except Exception as e:
        log_error(f"Error finding or terminating http.server processes: {e}")
    return []

if __name__ == "__main__":
    import sys
    start_reportor(sys.argv[1])