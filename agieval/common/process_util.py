import os
import json
import traceback
import shutil


from agieval.entity.eval_config import EvalConfig
from agieval.common.logger import log_error


PID_FILE_PATH = "/tmp/agieval_pid"

class ProcessContext:
    def __init__(self, eval_config: EvalConfig):
        self.eval_config = eval_config
        self.pid = str(os.getpid())

    def __enter__(self):
        check_work_dir(self.eval_config)
        create_base_path(self.pid)
        save_eval_config(self.pid, self.eval_config)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                log_error(traceback.format_exc())
                
            message = ""
            excetion_messages = load_excetion_message(self.pid)
            for pid, excetion_message in excetion_messages.items():
                log_error(f"Subprocess {pid} exception: {excetion_message[1]}")
                message = message + f"Subprocess {pid} exception: {excetion_message[0]}\n"

            if message:
                raise Exception(message)
        finally:
            delete_base_path(self.pid)
        

class SubProcessContext:
    def __init__(self, parent_pid):
        self.parent_pid = parent_pid
        self.pid = str(os.getpid())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return
        traceback_message = traceback.format_exc()
        log_error(traceback_message)
        save_sub_process_exception(self.parent_pid, self.pid, str(exc_val), traceback_message)
        


def check_work_dir(eval_config: EvalConfig):
    running_eval_configs = load_eval_config()
    for pid, running_eval_config in running_eval_configs.items():
        if running_eval_config["work_dir"] == eval_config.work_dir:
            raise Exception(f"work_dir: {eval_config.work_dir} is occupied by process {pid}")

def build_pid_path(pid):
    return os.path.join(PID_FILE_PATH, pid)

def create_base_path(pid):
    os.makedirs(build_pid_path(pid), exist_ok=True)

def delete_base_path(pid):
    pid_path = build_pid_path(pid)
    try:
        shutil.rmtree(pid_path)
    except Exception:
        pass


def build_pid_file_path(parent_pid, pid):
    suffix = "pid" if parent_pid == pid else "sub.pid"
    return os.path.join(build_pid_path(parent_pid), f"{pid}.{suffix}")

def create_pid_file(parent_pid, pid):
    pid_file = build_pid_file_path(parent_pid, pid)
    if os.path.exists(pid_file):
        return pid_file
    
    with open(pid_file, 'w') as f:
        pass
    return pid_file

def save_eval_config(pid, eval_config: EvalConfig):
    pid_file = create_pid_file(pid, pid)
    with open(pid_file, 'w') as f:
        json.dump(eval_config.model_dump(), f, indent=4, ensure_ascii=False)

def save_sub_process_exception(parent_pid, pid, message, traceback_message):
    pid_file = create_pid_file(parent_pid, pid)
    with open(pid_file, 'w') as f:
        f.write(message)
        f.write("\n-------\n")
        f.write(traceback_message)



def get_all_pids():
    if not os.path.exists(PID_FILE_PATH):
        return []
    return os.listdir(PID_FILE_PATH)


def load_eval_config():
    pids = get_all_pids()
    eval_configs = {}
    for pid in pids:
        pid_file = build_pid_file_path(pid, pid)
        with open(pid_file, 'r') as f:
            try:
                eval_config = json.load(f)
                eval_configs[str(pid)] = eval_config
            except Exception:
                eval_configs[str(pid)] = {}
    return eval_configs

def load_excetion_message(pid):
    pid_path = build_pid_path(pid)
    if not os.path.exists(pid_path):
        return {}
    
    sub_pids = []
    for filename in os.listdir(pid_path):
        if filename.endswith(".sub.pid"):
            try:
                sub_pids.append(filename[:-8])
            except ValueError:
                # If the filename is not a valid PID format, skip
                continue

    excetions = {}
    for sub_pid in sub_pids:
        sub_pid_file = build_pid_file_path(pid, sub_pid)
        try:
            with open(sub_pid_file, 'r') as f:
                content = f.read()

            parts = content.split("-------", 1)
            msg = parts[0].strip() if len(parts) > 0 else ""
            exc = parts[1].strip() if len(parts) > 1 else ""

            excetions[str(sub_pid)] = (msg, exc)
        except Exception:
                pass

    return excetions

