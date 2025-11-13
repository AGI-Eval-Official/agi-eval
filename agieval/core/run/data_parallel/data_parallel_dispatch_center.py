from multiprocessing.managers import SyncManager
from agieval.common.logger import log, log_error
from agieval.core.run.dispatch_center import DispatchCenter
from agieval.core.run.runner import Runner
from agieval.entity.eval_config import EvalConfig
from agieval.entity.flow_config import BenchmarkConfig


class DataParallelDispatchCenter(DispatchCenter):

    def __init__(self, eval_config: EvalConfig, benchmark_configs: list[BenchmarkConfig]):
        super().__init__(eval_config=eval_config, benchmark_configs=benchmark_configs)
        self.benchmark_retry_times = 2
        self.shared_param_ready = False


    def get_benchmark(self) -> BenchmarkConfig | None:
        data = None
        try:
            data = self.benchmark_queue.get_nowait()
        except Exception as e:
            if type(e).__name__ == "Empty":
               log("Dataset queue is empty")
            else:
                log_error(f"Dataset acquisition exception, process {self.get_process_id()} {e}")
        return data

    def allocate_benchmark(self, benchmark: BenchmarkConfig, runner: Runner):
        with self.assignment_lock:
            if benchmark.benchmark not in self.benchmark_allocation:
                self.benchmark_allocation[benchmark.benchmark] = [runner.__class__.__name__]
            else:
                list = self.benchmark_allocation[benchmark.benchmark] 
                list.append(runner.__class__.__name__)
                self.benchmark_allocation[benchmark.benchmark] = list

    def finish_benchmark(self, benchmark: BenchmarkConfig):
        with self.assignment_lock:
            self.benchmark_finished.append(benchmark.benchmark)

    def retry_benchmark(self, benchmark: BenchmarkConfig):
        with self.assignment_lock:
            if len(self.benchmark_allocation[benchmark.benchmark]) < self.benchmark_retry_times:
                self.benchmark_queue.put(benchmark)
                return True
            return False
        

    def get_shared_param(self, manager: SyncManager) -> dict:
        if not self.shared_param_ready: 
            self.benchmark_queue = manager.Queue()
            self.assignment_lock = manager.Lock()
            self.benchmark_allocation = manager.dict()
            self.benchmark_finished = manager.list()
            for benchmark in self.benchmark_configs:
                self.benchmark_queue.put(benchmark)
            self.shared_param_ready = True
        return {
            "benchmark_queue": self.benchmark_queue,
            "assignment_lock": self.assignment_lock,
            "benchmark_allocation": self.benchmark_allocation,
            "benchmark_finished": self.benchmark_finished
        }
    def restore_shared_param(self, **kwargs):
        if not self.shared_param_ready:
            self.benchmark_queue = kwargs["benchmark_queue"]
            self.assignment_lock = kwargs["assignment_lock"]
            self.benchmark_allocation = kwargs["benchmark_allocation"]
            self.benchmark_finished =  kwargs["benchmark_finished"]
            self.shared_param_ready = True
    
    def init_runners(self) -> list[type[Runner]]:
        # Delayed import to avoid circular dependency issues
        data_parallel = min(self.eval_config.data_parallel, len(self.benchmark_configs))
        from agieval.core.run.data_parallel.data_parallel_runner import DataParallelRunner
        return [DataParallelRunner for i in range(data_parallel)]
    
    def post_process(self):
        super().post_process()
        if len(self.benchmark_finished) == len(self.benchmark_configs):
            log("All datasets have been completed")
            return
        finished_benchmark = [benchmark for benchmark in self.benchmark_finished]
        un_finished_benchmark = [benchmark.benchmark for benchmark in self.benchmark_configs if benchmark.benchmark not in finished_benchmark]
        log_error(f"################  Note: The following datasets are not completed:\n {un_finished_benchmark}")


