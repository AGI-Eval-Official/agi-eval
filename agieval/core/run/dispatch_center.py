from __future__ import annotations
import multiprocessing
from multiprocessing.managers import SyncManager
import traceback
import signal
import os

from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

from agieval.common.logger import log, log_error, setup_logger
from agieval.common.cache import Cache
from agieval.common.process_util import SubProcessContext
from agieval.core.plugin.base_plugin import BasePlugin
from agieval.core.run.runner_type import RunnerType
from agieval.core.plugin.plugin_factory import PluginFactory
from agieval.entity.eval_config import EvalConfig
from agieval.entity.flow_config import BenchmarkConfig, FlowStage, PluginType


if TYPE_CHECKING:
    from agieval.core.run.runner import Runner

def async_worker(parent_pid: str, runner_class_name: type[Runner], eval_config: EvalConfig, benchmark_configs: list[BenchmarkConfig], **kwargs):
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # Restore default handling
    signal.signal(signal.SIGTERM, signal.SIG_DFL)

    def signal_handler(sig, frame):
        log(f"Received signal {sig}, exiting current process")
        # TODO: Actively clean up resources and exit process
        os._exit(0)
    signal.signal(signal.SIGTERM, signal_handler)

    setup_logger(eval_config.work_dir, debug=eval_config.debug, switch_log_file=False)
    with SubProcessContext(parent_pid):
        runner = runner_class_name(eval_config, benchmark_configs)
        runner.dispatch_center.restore_shared_param(**kwargs)
        runner.run()

exit_signal = False
processes: dict[multiprocessing.Process, type[Runner]] = {}

def signal_handler(sig, frame):
    log(f"Received signal {sig}, shutting down gracefully...")
    global exit_signal
    exit_signal = True
    terminate_all_processes()

def terminate_all_processes():
    """
    Terminate all child processes
    """
    global processes
    for process, runner in processes.items():
        if process.is_alive():
            log(f"Terminating child process {process.pid} belonging to Runner {runner.__name__}...")
            process.terminate()
    for process, runner in processes.items():
        # Ensure process is terminated
        try:
            process.join(timeout=0.5)
            if process.is_alive():
                log_error(f"Child process {process.pid} belonging to Runner {runner.__name__} cannot terminate itself, attempting forced termination")
                # Use SIGKILL to force termination on Unix systems
                try:
                    os.kill(process.pid, signal.SIGKILL)
                except:
                    pass
        except:
            pass
    log("All child processes have been terminated")


class DispatchCenter(ABC):
    def __init__(self, eval_config: EvalConfig, benchmark_configs: list[BenchmarkConfig]):
        self.eval_config: EvalConfig = eval_config
        self.benchmark_configs: list[BenchmarkConfig] = benchmark_configs


    @staticmethod
    def init(eval_config: EvalConfig, benchmark_configs: list[BenchmarkConfig]) -> "DispatchCenter":
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        Cache.init(eval_config.work_dir)
        Cache.save_eval_config(eval_config.model_dump())
        Cache.save_benchmark_configs([benchmark_config.model_dump() for benchmark_config in benchmark_configs])

        dispatch_center = None
        if eval_config.runner == RunnerType.LOCAL:
            from agieval.core.run.local.local_dispatch_center import LocalDispatchCenter
            dispatch_center = LocalDispatchCenter(eval_config, benchmark_configs)
        elif eval_config.runner == RunnerType.DATA_PARALLEL:
            from agieval.core.run.data_parallel.data_parallel_dispatch_center import DataParallelDispatchCenter
            dispatch_center = DataParallelDispatchCenter(eval_config, benchmark_configs)
        else:
            dispatch_center = DummyDispatchCenter(eval_config, benchmark_configs)
        return dispatch_center
    
    
    def start(self):
        """
        Dispatch center starts execution
        Depending on the scheduling method, different Runners are instantiated for execution
        Runner interacts with the dispatch center, receives tasks, executes tasks, and callbacks task results
        """
        with multiprocessing.Manager() as manager:
            try:
                # Initialize runners by subclass
                log("Starting to initialize runners...")
                runners = self.init_runners()
                log(f"Initialization completed, there are {len(runners)} runners in total")

                # Submit runner to child process for execution
                for idx, runner in enumerate(runners):
                    self.submit_runner(idx, runner, manager)

                # Wait for all runners to complete execution
                log("Waiting for all runners to complete execution...")
                self.wait_all_runners()
                log("All runners have completed execution")
                
                log("Post-processing started...")
                self.post_process()
                log("Post-processing completed...")
            except KeyboardInterrupt:
                log_error("Interrupt signal received, all child processes have been terminated")
            except Exception as e:
                log_error(f"Exception occurred during execution: {str(e)}")
                log_error(traceback.format_exc())
                # Terminate all child processes
                terminate_all_processes()
                # Re-raise the exception
                raise
        log("DispatchCenter finished")
        
    @abstractmethod
    def init_runners(self) -> list[type[Runner]]:
        """
        By subclass implementation, instantiate all required runners

        Returns:
            list[type[Runner]]: runner list
        """
        pass

    def submit_runner(self, idx, runner: type[Runner], manager: SyncManager):
        global processes
        """
        Submit a runner, add it to the runners list and execute it in a child process

        Args:
            runner: Runner to be executed
        """
        # Create child process to execute runner's run method
        process = self.process(idx, runner, manager)
        processes[process] = runner
        # Start child process
        process.start()
        log(f"<<<<<<<<< Runner {runner.__name__} has been submitted to child process {process.pid} for execution")

    def process(self, idx, runner: type[Runner], manager: SyncManager):
        return multiprocessing.Process(
            name=f"{runner.__name__}-{idx + 1}",
            target=async_worker, 
            args=(str(os.getpid()), runner, self.eval_config, self.benchmark_configs),
            kwargs=self.get_shared_param(manager)
        )

    @abstractmethod
    def get_shared_param(self, manager: SyncManager) -> dict:
        pass
    @abstractmethod
    def restore_shared_param(self, **kwargs):
        pass
        
    def wait_all_runners(self):
        """
        Wait for all runners to complete execution
        """
        while True:
            global exit_signal, processes
            alive_processes: dict[multiprocessing.Process, type[Runner]] = {}
            for process, runner in processes.items():
                try:
                    if process.is_alive():
                        alive_processes[process] = runner
                        process.join(0.5)
                    else:
                        log(f">>>>>>>>> Child process {process.pid} belonging to Runner {runner.__name__} has completed execution")
                except KeyboardInterrupt:
                    pass
            processes = alive_processes
            if not processes:
                break

        if exit_signal:
            raise KeyboardInterrupt


    def post_process(self):
        pass


        
    def get_process_id(self):
        return multiprocessing.current_process().pid
    
    def execute_stage(self, runner: Runner, benchmark_config: BenchmarkConfig, flow_stage: FlowStage, eval_config: EvalConfig):

        PluginFactory.find_plugin(
            plugin_implement=flow_stage.plugin_implement,
            context_params=flow_stage.context_params
        )

        plugin_type = flow_stage.plugin_type
        if plugin_type is None or plugin_type == PluginType.NONE_TYPE:
            stage_plugin = PluginFactory[BasePlugin].get_plugin_by_name(plugin_name=flow_stage.plugin_implement)
            plugin_type = stage_plugin.plugin_type
        
        log(f">>>>>>> Execution unit 【{benchmark_config.benchmark}】, Stage 【{flow_stage.stage}】start")
        if plugin_type == PluginType.STAGE_DATA_PROCESSOR:
            from agieval.plugin.stage.data.data_processor import DataProcessor
            data_processor = PluginFactory[DataProcessor].get_plugin_by_name(plugin_name=flow_stage.plugin_implement)
            data_processor.run(flow_stage.plugins, eval_config)
        elif plugin_type == PluginType.STAGE_INFER_PROCESSOR:
            from agieval.plugin.stage.infer.infer_processor import InferProcessor
            infer_processor = PluginFactory[InferProcessor].get_plugin_by_name(plugin_name=flow_stage.plugin_implement)
            infer_processor.run(flow_stage.plugins, eval_config)
        elif plugin_type == PluginType.STAGE_METRICS_PROCESSOR:
            from agieval.plugin.stage.metrics.metrics_processor import MetricsProcessor
            metrics_processor = PluginFactory[MetricsProcessor].get_plugin_by_name(plugin_name=flow_stage.plugin_implement)
            metrics_processor.run(flow_stage.plugins, eval_config)
        elif plugin_type == PluginType.STAGE_REPORT_PROCESSOR:
            from agieval.plugin.stage.report.report_processor import ReportProcessor
            report_processor = PluginFactory[ReportProcessor].get_plugin_by_name(plugin_name=flow_stage.plugin_implement)
            report_processor.run(flow_stage.plugins, eval_config)
        log(f"<<<<<<< Execution unit 【{benchmark_config.benchmark}】, Stage 【{flow_stage.stage}】end\n")


class DummyDispatchCenter(DispatchCenter):
    def start(self):
        log("DummyDispatchCenter is only used to generate complete evaluation dataset configuration files, does not execute evaluation tasks")
        
    def get_shared_param(self, manager: SyncManager) -> dict:
        return {}
    def restore_shared_param(self, **kwargs):
        pass
    def init_runners(self) -> list[type[Runner]]:
        # Delayed import to avoid circular dependency issues
        from agieval.core.run.runner import DummyRunner
        return [DummyRunner]


