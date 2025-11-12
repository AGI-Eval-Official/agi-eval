from enum import Enum

class RunnerType(str, Enum):
    DUMMY = "dummy"
    LOCAL = "local"
    DATA_PARALLEL = "data_parallel"