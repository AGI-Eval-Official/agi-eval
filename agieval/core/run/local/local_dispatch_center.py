from __future__ import annotations
from multiprocessing.managers import SyncManager
from typing import List, Tuple, TYPE_CHECKING

from agieval.core.run.dispatch_center import DispatchCenter
from agieval.core.run.runner import Runner
from agieval.entity.eval_config import EvalConfig
from agieval.entity.flow_config import FlowStage, BenchmarkConfig

if TYPE_CHECKING:
    from agieval.core.run.runner import Runner

class LocalDispatchCenter(DispatchCenter):

    def __init__(self, eval_config: EvalConfig, benchmark_configs: List[BenchmarkConfig]):
        super().__init__(eval_config=eval_config, benchmark_configs=benchmark_configs)

        self.finished_benchmarks: List[BenchmarkConfig] = []
        self.current_benchmark: BenchmarkConfig | None = None
        
        self.un_start_stages: List[FlowStage] = []
        self.finished_stages: List[Tuple[str, FlowStage]] = []
        self.current_stage: FlowStage | None = None
    

    def has_stage(self) -> bool:
        return self.current_stage is not None


    def dispatch_start(self):
        self.next_benchmark()
        self.next_stage()

    def next_benchmark(self):
        self.refresh_finished_benchmarks()

        if len(self.benchmark_configs) > 0:
            self.current_benchmark = self.benchmark_configs.pop(0)
            self.un_start_stages = [stage_config for stage_config in self.current_benchmark.flow_stages]

            
    def refresh_finished_benchmarks(self):
        if self.current_benchmark is None:
            return
        self.finished_benchmarks.append(self.current_benchmark)
        self.current_benchmark = None

    def refresh_finished_stages(self):
        if self.current_stage is None:
            return
        assert self.current_benchmark is not None, "Dispatch exception, benchmark is empty"
        self.finished_stages.append((self.current_benchmark.benchmark, self.current_stage))
        self.current_stage = None


    def next_stage(self):
        self.refresh_finished_stages()

        if len(self.un_start_stages) == 0:
            self.next_benchmark()

        if len(self.un_start_stages) > 0:
            self.current_stage = self.un_start_stages.pop(0)
            self.un_start_steps = self.current_stage.plugins


    def get_shared_param(self, manager: SyncManager) -> dict:
        return {}
    def restore_shared_param(self, **kwargs):
        pass
    def init_runners(self) -> list[type[Runner]]:
        # Delayed import to avoid circular dependency issues
        from agieval.core.run.local.local_runner import LocalRunner
        return [LocalRunner]
