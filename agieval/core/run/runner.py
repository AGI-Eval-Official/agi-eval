from abc import ABC, abstractmethod

import traceback
from typing import Generic, TypeVar, get_args, get_origin, cast

from agieval.common.logger import log, log_error
from agieval.core.run.dispatch_center import DispatchCenter
from agieval.common.cache import Cache
from agieval.entity.eval_config import EvalConfig
from agieval.entity.flow_config import BenchmarkConfig


T = TypeVar('T', bound=DispatchCenter)  # Define generic type, limited to DispatchCenter subclasses
class Runner(ABC, Generic[T]):

    def __init__(self, eval_config: EvalConfig, benchmark_configs: list[BenchmarkConfig]):
        # Process of getting generic parameters
        assert hasattr(self.__class__, "__orig_bases__"), "Runner implementation class definition does not conform to specifications"
        orig_bases = getattr(self.__class__, "__orig_bases__")
        assert len(orig_bases) > 0, "Runner implementation class definition does not conform to specifications"
        orig_base = orig_bases[0]
        assert issubclass(get_origin(orig_base), Runner), "Runner implementation class definition does not conform to specifications"
        generic_args = get_args(orig_base)
        assert len(generic_args) > 0, "Runner implementation class definition does not conform to specifications"
        dispatch_center_class = generic_args[0]
        assert issubclass(dispatch_center_class, DispatchCenter), "Runner implementation class definition does not conform to specifications"
        dispatch_center_class = cast(type[T], dispatch_center_class)
        self.dispatch_center = dispatch_center_class(eval_config, benchmark_configs)
        Cache.init(self.dispatch_center.eval_config.work_dir)
    
    def run(self):
        Cache.init(self.dispatch_center.eval_config.work_dir)
        log(f"Runner {self.__class__.__name__} run start")
        try:
            self.do_run()
        except Exception as e:
            log_error(f"Runner {self.__class__.__name__} run excetion, {e}, {traceback.format_exc()}")
            raise e
        log(f"Runner {self.__class__.__name__} run finished")
        
    @abstractmethod
    def do_run(self):
        """
        Actual evaluation execution logic
        """
        pass


class DummyRunner(Runner):

    def do_run(self):
        print("DummyRunner run")