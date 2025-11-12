import os
import datetime
import logging
import inspect
from concurrent_log_handler import ConcurrentRotatingFileHandler

LOG_PATH = "logs"
INFO_LOG_FILE = "info.log"
REAL_INFO_LOG_FILE = "info-{:}.log"
DEBUG_LOG_FILE = "debug.log"
REAL_DEBUG_LOG_FILE = "debug-{:}.log"
ERROR_LOG_FILE = "error.log"
REAL_ERROR_LOG_FILE = "error-{:}.log"


"""
Log utility
"""
logger = logging.getLogger()

class SmartFormatter(logging.Formatter):
    def __init__(self, datefmt=None):
        self.caller_format = '%(asctime)s - %(levelname)s - %(processName)s(%(process)d) - %(caller_filename)s:%(caller_lineno)d - %(message)s'
        self.default_format = '%(asctime)s - %(levelname)s - %(processName)s(%(process)d) - %(filename)s:%(lineno)d - %(message)s'
        super().__init__(fmt=self.default_format, datefmt=datefmt)

    def format(self, record):
        has_caller_filename = hasattr(record, 'caller_filename') and getattr(record, 'caller_filename') is not None
        has_caller_lineno = hasattr(record, 'caller_lineno') and getattr(record, 'caller_lineno') is not None

        if has_caller_filename and has_caller_lineno:
            self._style._fmt = self.caller_format
        else:
            self._style._fmt = self.default_format

        return super().format(record)


def setup_logger(work_dir: str, debug = False, switch_log_file = True):
    os.makedirs(os.path.join(work_dir, LOG_PATH), exist_ok=True)

    info_log_file_path = os.path.join(work_dir, LOG_PATH, INFO_LOG_FILE)
    debug_log_file_path = os.path.join(work_dir, LOG_PATH, DEBUG_LOG_FILE)
    error_log_file_path = os.path.join(work_dir, LOG_PATH, ERROR_LOG_FILE)

    logger_leval = logging.DEBUG if debug else logging.INFO
    logger.setLevel(logger_leval)

    info_file_handler: ConcurrentRotatingFileHandler = ConcurrentRotatingFileHandler(info_log_file_path, encoding="utf-8")
    debug_file_handler: ConcurrentRotatingFileHandler = ConcurrentRotatingFileHandler(debug_log_file_path, encoding="utf-8")
    error_file_handler: ConcurrentRotatingFileHandler = ConcurrentRotatingFileHandler(error_log_file_path, encoding="utf-8")
    handler = logging.StreamHandler()

    formatter = SmartFormatter(datefmt='%Y-%m-%d %H:%M:%S')

    info_file_handler.setFormatter(formatter)
    info_file_handler.setLevel(logging.INFO)

    debug_file_handler.setFormatter(formatter)
    debug_file_handler.setLevel(logging.DEBUG)

    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)

    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)

    if not switch_log_file:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    logger.addHandler(info_file_handler)
    logger.addHandler(debug_file_handler)
    logger.addHandler(error_file_handler)
    logger.addHandler(handler)

    if not switch_log_file:
        return

    
    datetime_str = datetime.datetime.now().strftime("%Y%m%d@%H%M%S")
    real_info_log_file = REAL_INFO_LOG_FILE.format(datetime_str)
    real_debug_log_file = REAL_DEBUG_LOG_FILE.format(datetime_str)
    real_error_log_file = REAL_ERROR_LOG_FILE.format(datetime_str)
    switch_log(work_dir, info_log_file_path, real_info_log_file)
    switch_log(work_dir, debug_log_file_path, real_debug_log_file)
    switch_log(work_dir, error_log_file_path, real_error_log_file)
    log(f"{INFO_LOG_FILE} log file has been switched to {real_info_log_file}")
    log(f"{DEBUG_LOG_FILE} log file has been switched to {real_debug_log_file}")
    log(f"{ERROR_LOG_FILE} log file has been switched to {real_error_log_file}")

def switch_log(work_dir, log_file_path, real_log_file):
    if os.path.exists(log_file_path):
        assert os.path.islink(log_file_path), f"Log file {log_file_path} already exists"
        os.unlink(log_file_path)

    real_log_file_path = os.path.join(work_dir, LOG_PATH, real_log_file)
    open(real_log_file_path, "w").close()
    os.symlink(real_log_file, log_file_path)


def _get_caller_info():
    """Get caller's filename and line number"""
    # Get call stack: current function -> log function -> real caller
    frame = inspect.currentframe().f_back.f_back
    method_name = os.path.basename(frame.f_code.co_name)
    if method_name in ["log", "log_debug", "log_warn", "log_error"]:
       frame = inspect.currentframe().f_back.f_back.f_back
    filename = os.path.basename(frame.f_code.co_filename)
    lineno = frame.f_lineno
    return {'caller_filename': filename, 'caller_lineno': lineno}


def log(x):
    logger.info(str(x), extra=_get_caller_info())

def log_debug(x):
    logger.debug(str(x), extra=_get_caller_info())

def log_warn(x):
    logger.warning(str(x), extra=_get_caller_info())

def log_error(x):
    logger.error(str(x), extra=_get_caller_info())


if __name__ == "__main__":
    log("hello world")
    log_error("This is an error msg")
