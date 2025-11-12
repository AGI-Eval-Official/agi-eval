import json
import os
import time
from dataclasses import is_dataclass, asdict
from typing import cast, List

import dacite
import portalocker

from agieval.entity.scenario_state import ScenarioState
from agieval.entity.stat import PerInstanceStats, Stat
from agieval.common.logger import log, log_error
from agieval.common.constant import RUNTIME_PARAM_EVAL_CONFIG_FILE, RUNTIME_PARAM_BENCHMARK_CONFIG_FILE, FILE_STAT, FILE_PER_INSTANCE_STATS, FILE_SCENARIO_STATE



class Cache:
    """
    Cache processing utility class
    Mainly used for cache read and write
    """
    work_dir = "result/tmp"
    file_lock = None

    @classmethod
    def init(cls,work_dir):
        cls.work_dir = work_dir
        
    @classmethod
    def save_eval_config(cls, object):
        cls.save(object, RUNTIME_PARAM_EVAL_CONFIG_FILE, "")
        
    @classmethod
    def save_benchmark_configs(cls, object):
        cls.save(object, RUNTIME_PARAM_BENCHMARK_CONFIG_FILE, "")
        
    @classmethod
    def save_stats(cls, object, benchmark_id: str):
        cls.save(object, FILE_STAT, benchmark_id)
        
    @classmethod
    def save_per_instance_stat(cls, object, benchmark_id: str):
        cls.save(object, FILE_PER_INSTANCE_STATS, benchmark_id)
        
    @classmethod
    def save_scenario_state(cls, object, benchmark_id: str):
        cls.save(object, FILE_SCENARIO_STATE, benchmark_id)
        
    @classmethod
    def save(cls, object, relative_path, benchmark_id: str):
        dir_path = cls.get_result_path(benchmark_id)
        os.makedirs(dir_path, exist_ok=True)
        path = os.path.join(dir_path, relative_path)
        # Choose file opening mode.
        # By default, use r+ to prevent w mode from clearing the file when opening but not acquiring the lock. Only create lock when creating new file
        mode = 'r+'
        if not os.path.exists(path):
            with open(path, 'w') as f:
                pass
        with open(path, mode, encoding='utf-8') as f:
            try:
                # Lock exclusive lock
                portalocker.lock(f, portalocker.LOCK_EX)
                # Manually clear content to prevent incomplete writing under r+
                f.truncate()
                # Write new content
                if isinstance(object, list):
                    data = [cls.as_dict(o) for o in object]
                else:
                    data = cls.as_dict(object)
                # if encrypt_flag:
                #     data = auto_encrypt(data)
                json.dump(data, f, indent=4, ensure_ascii=False)
                log(f"Saving data to: {path}")
                log(f"File size after saving: {f.tell()} bytes")
            finally:
                # Force release lock
                portalocker.unlock(f)

    @classmethod
    def get_result_path(cls, benchmark_id: str):
        return os.path.join(cls.work_dir, benchmark_id)

    @classmethod
    def load_stats(cls, benchmark_id: str, default_value=None) -> list[Stat] | None:
        stats = cls.load(FILE_STAT, benchmark_id, default_value=default_value, target_class=None)
        if stats is None:
            return None
        return [cls.as_dataclass(stat, Stat) for stat in stats]

    @classmethod
    def load_per_instance_stats(cls, benchmark_id: str, default_value=None) -> List[PerInstanceStats]:
        stats = cls.load(FILE_PER_INSTANCE_STATS, benchmark_id, default_value=default_value, target_class=None)
        if stats is None:
            return None
        return [cls.as_dataclass(stat, PerInstanceStats) for stat in stats]

    @classmethod
    def load_scenario_state(cls, benchmark_id: str, default_value=None) -> ScenarioState:
        return cast(ScenarioState, cls.load(FILE_SCENARIO_STATE, benchmark_id, default_value=default_value, target_class=ScenarioState))
    
    
    @classmethod
    def load(cls, relative_path, benchmark_id: str, default_value=None, target_class=None):
        # Concatenate absolute path
        dir_path = cls.get_result_path(benchmark_id)
        path = os.path.join(dir_path, relative_path)
        mode = 'r'
        # When file does not exist, return specified default value
        if not os.path.exists(path):
            return default_value
        retry = 0
        while True:
            with open(path, mode, encoding='utf-8') as f:
                try:
                    # Lock read lock only
                    portalocker.lock(f, portalocker.LOCK_EX)
                    # Read new content
                    data = f.read()
                    # data = auto_decrypt(data)
                    data = json.loads(data)
                    break
                except Exception as e:
                    retry += 1
                    log_error(f"Error loading file: {path}, retry {retry}...{e}")
                    if retry<4:
                        time.sleep(5)
                        continue
                    return default_value
                finally:
                    # Force release lock
                    portalocker.unlock(f)

        # If needed, convert to corresponding dataclass instance
        if target_class is not None:
            return cls.as_dataclass(data, target_class)
        return data
   

    @staticmethod
    def as_dict(obj):
        """
        Convert dataclass to dict
        :param obj:
        :return:
        """
        if not is_dataclass(obj):
            return obj
        return asdict(obj, dict_factory=lambda x: {k: v for (k, v) in x if v is not None})
    @staticmethod
    def as_dataclass(obj, target_class):
        """
        Convert dict to dataclass
        :param obj:
        :param target_class:
        :return:
        """
        return dacite.from_dict(data_class=target_class, data=obj)


