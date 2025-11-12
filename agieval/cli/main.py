import os
from typing import List, Optional
from argparse import ArgumentParser
import importlib.util

from agieval.common.logger import setup_logger, log, log_error
from agieval.core.run.runner_type import RunnerType
from agieval.core.run.dispatch_center import DispatchCenter
from agieval.entity.eval_config import EvalConfig
from agieval.entity.flow_config import BenchmarkConfig
from agieval.entity.global_param import GlobalParam
from agieval.common.param_utils import load_benchmark_configs
from agieval.common.dataset_util import download_dataset_from_git, download_dataset_config, DATASET_CONFIG_FILE
from agieval.common.process_util import ProcessContext

def _parse_extra_param(extra_params: Optional[List[str]], group_name: str) -> dict:
    """Validate and parse key-value pair parameters"""
    if not extra_params:
        return {}
    
    param_dict = {}
    for param in extra_params:
        if '=' not in param:
            raise ValueError(f"Parameter group '{group_name}' format error: '{param}' must be in key=value format")
        
        key, *values = param.split('=', 1)  # Split only the first equals sign
        if not key or not values:
            raise ValueError(f"Parameter group '{group_name}' format error: '{param}' must be in key=value format")
        
        param_dict[key] = values[0]  # Take everything after the equals sign as the value
    
    return param_dict

def add_param_group(parser: ArgumentParser):
    extra_args_group = parser.add_argument_group('global_param', 'Global parameter group')
    extra_args_group.add_argument('--global_param', nargs='*', metavar='k1=v1 k2=v2', help='Accept any global parameters')
    extra_args_group = parser.add_argument_group('plugin_param', 'Plugin parameter group')
    extra_args_group.add_argument('--plugin_param', nargs='*', metavar='k1=v1 k2=v2', help='Accept any plugin parameters')



def parse_example_args(dataset, param) -> tuple[EvalConfig, BenchmarkConfig]:
    example_config_path = os.path.join("example/dataset", dataset, "config.py")
    example_module_name = os.path.join(f"example.dataset.{dataset}.config")

    download_dataset_config(dataset, os.path.join("example/dataset", dataset, DATASET_CONFIG_FILE))
    
    assert os.path.exists(example_config_path) and os.path.isfile(
        example_config_path), f"The specified dataset {dataset} is not adapted, please download the dataset offline and refer to the example configuration before use"
    spec = importlib.util.spec_from_file_location(
        example_module_name, example_config_path)
    assert spec is not None and spec.loader is not None, f"The specified example dataset configuration file {example_config_path} cannot be loaded"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    eval_config: EvalConfig = getattr(module, "eval_config")
    benchmark_config_template: BenchmarkConfig = getattr(module, "benchmark_config_template")

    parser = ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--runner", type=RunnerType, choices=[type for type in RunnerType], default=None, help="Scheduling method")
    parser.add_argument("--benchmark_config", type=str, default="", help="Evaluation dataset configuration")
    add_param_group(parser)
    args, _ = parser.parse_known_args(param)
    global_param_dict = _parse_extra_param(args.global_param, 'global_param')
    plugin_param_dict = _parse_extra_param(args.plugin_param, 'plugin_param')

    eval_config.global_param = eval_config.global_param.model_copy(update=global_param_dict)
    eval_config.plugin_param.update(plugin_param_dict)
    if args.runner is not None:
        eval_config.runner = args.runner
    if args.benchmark_config:
        eval_config.benchmark_config = args.benchmark_config

        
    assert eval_config.work_dir, "work_dir must be specified"
    assert eval_config.benchmark_config or (eval_config.benchmark_config_template and eval_config.dataset_files and benchmark_config_template), "Evaluation dataset configuration or template must be specified"

    return eval_config, benchmark_config_template


def _parse_args(param) -> EvalConfig:
    parser = ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--runner", type=RunnerType, choices=[type for type in RunnerType], default=RunnerType.DUMMY, help="Scheduling method")
    parser.add_argument("--benchmark_config_template", action="store_true", help="Use evaluation dataset configuration template, benchmark_config as template")
    parser.add_argument("--dataset_files", type=str, default="", help="Required when specifying eval_task_config_template, if it's a directory then read all .json files in the directory as actual datasets, if it's a file then each line should specify dataset file address")
    parser.add_argument("--benchmark_config", type=str, required=True, help="Evaluation dataset configuration")
    parser.add_argument("--flow_config_file", type=str, default="", help="Default evaluation process configuration for evaluation dataset")
    parser.add_argument("--work_dir", type=str, required=True, help="Cache directory, stores temporary data, evaluation results, etc.")
    parser.add_argument("--data_parallel", type=int, default=1, help="Concurrency for dataset parallelism")
    add_param_group(parser)
    args = parser.parse_args(param)
    try:
        # Validate and parse global parameters
        global_param_dict = _parse_extra_param(args.global_param, 'global_param')
        plugin_param_dict = _parse_extra_param(args.plugin_param, 'plugin_param')
        args.global_param = GlobalParam.model_validate(global_param_dict)
        args.plugin_param = plugin_param_dict
    except ValueError as e:
        parser.error(str(e))  # Will display help message and exit
    return EvalConfig.model_validate(vars(args))



def run_example_dataset(dataset, eval_config: EvalConfig, benchmark_config_template: BenchmarkConfig):
    setup_logger(eval_config.work_dir, eval_config.debug)
    with ProcessContext(eval_config):
        if eval_config.benchmark_config:
            eval_config.benchmark_config_template = False
            benchmark_configs = load_benchmark_configs(eval_config, eval_config.benchmark_config, "")
        else:
            eval_config.dataset_files = os.path.join(os.getcwd(), eval_config.dataset_files)
            if not download_dataset_from_git(dataset, eval_config.dataset_files):
                log_error("Dataset download failed, terminating subsequent evaluation process")
                raise Exception("Dataset download failed")
            benchmark_configs = load_benchmark_configs(eval_config, benchmark_config_template, "")
        
        run_with_eval_config(eval_config, benchmark_configs)

    
def run_custom_dataset(args):
    eval_config = _parse_args(args)
    setup_logger(eval_config.work_dir, eval_config.debug)
    with ProcessContext(eval_config):
        benchmark_configs = load_benchmark_configs(eval_config, eval_config.benchmark_config, eval_config.flow_config_file)
        run_with_eval_config(eval_config, benchmark_configs)
    

def run_with_eval_config(eval_config: EvalConfig, benchmark_configs: List[BenchmarkConfig]):
    log("\n\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Hyperparameter processing completed, loading DispatchCenter to start evaluation <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n\n\n")
    DispatchCenter.init(eval_config, benchmark_configs).start()


def main():
    parser = ArgumentParser()
    _, args = parser.parse_known_args()
    if not args or args[0].startswith('--'):
        run_custom_dataset(args)
    else:
        eval_config, eval_task_config = parse_example_args(args[0], args[1:])
        run_example_dataset(args[0], eval_config, eval_task_config)

if __name__ == "__main__":
    main()
    