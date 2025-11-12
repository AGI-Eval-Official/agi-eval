from argparse import ArgumentParser
import json
import os
import sys
import signal

from pathlib import Path
import time

import agieval
from agieval.cli.main import parse_example_args, run_example_dataset
from agieval.common.process_util import delete_base_path, get_all_pids, load_eval_config, check_work_dir
from agieval.common.logger import LOG_PATH, INFO_LOG_FILE
from agieval.common.dataset_util import get_datasets
from agieval.visualization.reportor import DEFAULT_PORT, start_reportor, stop_reportor

def chdir_root():
    root_path = Path(__file__).resolve().parent.parent.parent
    os.chdir(root_path)         


def start(args):
    try:
        pid = os.fork()
        if pid > 0:
            # Parent process exits
            sys.exit(0)
    except OSError as e:
        import traceback
        print(f"Failed to start evaluation task, process startup exception: {e}\n{traceback.format_exc()}")
        sys.exit(1)

    # Detach from parent process
    os.chdir("/")
    os.setsid()
    os.umask(0)

    # Second fork to ensure child process is not session leader
    try:
        pid = os.fork()
        if pid > 0:
            # Parent process exits
            sys.exit(0)
    except OSError as e:
        import traceback
        print(f"Failed to start evaluation task, process startup exception: {e}\n{traceback.format_exc()}")
        sys.exit(1)


    chdir_root()
    eval_config, eval_task_config = parse_example_args(args[0], args[1:])
    print(f"Task process started successfully pid: {os.getpid()}, log path: {os.path.join(os.getcwd(), eval_config.work_dir, LOG_PATH, INFO_LOG_FILE)}")
    check_work_dir(eval_config)
    
    # Redirect standard input, output, and error to /dev/null
    sys.stdin.flush()
    sys.stdout.flush()
    sys.stderr.flush()
    with open(os.devnull, 'r') as dev_null_r, \
         open(os.devnull, 'w') as dev_null_w:
        os.dup2(dev_null_r.fileno(), sys.stdin.fileno())
        os.dup2(dev_null_w.fileno(), sys.stdout.fileno())
        os.dup2(dev_null_w.fileno(), sys.stderr.fileno())
    run_example_dataset(args[0], eval_config, eval_task_config)



def stop(pids):
    all_pids = get_all_pids()
    if not pids:
        pids = all_pids
    else:
        pids = [pid for pid in pids if pid in all_pids]
    if not pids:
        print("No AGI-Eval task stoped.")
        return

    print(f"Starting to stop evaluation tasks: {', '.join(pids)}")
    wait_pids = []
    for pid in pids:
        try:
            os.kill(int(pid), 0)
            os.kill(int(pid), signal.SIGTERM)  # SIGTERM
        except PermissionError:
            print(f"Permission denied, pid {pid}")
            continue
        except OSError:
            pass
        wait_pids.append(pid)

    killed_pids = []
    while True:
        for pid in wait_pids:
            try:
                os.kill(int(pid), 0)
                continue
            except OSError:
                killed_pids.append(pid)
                delete_base_path(pid)
                print(f"Evaluation task stopped: {pid}")
        if len(killed_pids) == len(wait_pids):
           break
        time.sleep(1)
    print("All evaluation tasks have been stopped")


def status():
    all_pids = get_all_pids()
    if not all_pids:
        print("No AGI-Eval task is running.")
        return

    print(f"AGI-Eval running task pids: {', '.join(all_pids)}")
    
    eval_configs = load_eval_config()
    print(f"AGI-Eval running task configs:\n {json.dumps(eval_configs, indent=4, ensure_ascii=False)}")



def main():
    parser = ArgumentParser('AGI-Eval Command Line tool', usage='agieval <command> [<args>]')
    parser.add_argument('-v', '--version', action='version', version=f'AGI-Eval {agieval.__version__}')
    subparsers = parser.add_subparsers(dest='command', help='AGI-Eval command line helper.')

    subparsers.add_parser('start', help='Start AGI-Eval server.', usage="agieval start <benchmark> [options]")
    
    stop_parser = subparsers.add_parser('stop', help='Stop AGI-Eval server.', usage="agieval stop [pids]")
    stop_parser.add_argument("pids", nargs='*', help="PIDs of evaluation tasks to terminate, default terminates all evaluation tasks")

    subparsers.add_parser('status', help='return AGI-Eval task status.', usage="agieval status")

    subparsers.add_parser('benchmarks', help='return the adapted benchmarks.', usage="agieval benchmarks")

    app_start_parser = subparsers.add_parser('appstart', help='Start AGI-Eval visualization server.', usage="agieval appstart <result_dir> [options]")
    app_start_parser.add_argument("--result_dir", type=str, required=True, help="Evaluation result directory")
    app_start_parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Service port, default {DEFAULT_PORT}")

    subparsers.add_parser('appstop', help='Stop AGI-Eval visualization server.', usage="agieval appstop")

    sub_command, args = parser.parse_known_args()

    chdir_root()
    if sub_command.command == 'start':
        benchmarks = get_datasets()
        assert args and args[0] in benchmarks, f"Only the following adapted datasets are supported\n{', '.join(benchmarks)}"
        start(args)
    elif sub_command.command == 'stop':
        stop(sub_command.pids)
    elif sub_command.command == 'status':
        status()
    elif sub_command.command == 'benchmarks':
        benchmarks = get_datasets()
        print(f"Adapted benchmarks:\n{', '.join(benchmarks)}")
    elif sub_command.command == 'appstart':
        url = start_reportor(sub_command.result_dir, sub_command.port)
        if url:
            print(f"Visit the following URL to view the evaluation report: {url}")
    elif sub_command.command == 'appstop':
        killed_pids = stop_reportor()
        print(f"Evaluation result visualization service stopped: {', '.join(killed_pids)}")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
