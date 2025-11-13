from agieval.common.logger import log
from agieval.core.run.data_parallel.data_parallel_dispatch_center import DataParallelDispatchCenter
from agieval.core.run.runner import Runner


class DataParallelRunner(Runner[DataParallelDispatchCenter]):

    def do_run(self):
        benchmark = self.dispatch_center.get_benchmark()
        while benchmark:
            log(f"Dataset acquired {benchmark.benchmark}")
            try:
                self.dispatch_center.allocate_benchmark(benchmark, self)
                for flow_stage in benchmark.flow_stages:
                    self.dispatch_center.execute_stage(self, benchmark, flow_stage, self.dispatch_center.eval_config)
                self.dispatch_center.finish_benchmark(benchmark)
            except Exception as e:
                if not self.dispatch_center.retry_benchmark(benchmark):
                    raise Exception(f"Dataset {benchmark.benchmark} execution exception, {str(e)}") from e

            benchmark = self.dispatch_center.get_benchmark()


            