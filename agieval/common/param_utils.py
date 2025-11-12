import copy
import inspect
import os
import json
from pathlib import Path
from typing import Any

from agieval.core.plugin.base_plugin_param import BasePluginParam
from agieval.entity.eval_config import EvalConfig
from agieval.entity.flow_config import BenchmarkConfig, FlowStage, PluginConfig, ContextParam, PluginType
from agieval.core.plugin.plugin_factory import PluginFactory
from agieval.core.plugin.base_plugin import BasePlugin, BaseStage, BaseStep
from agieval.common.exception import FlowConfigParseException, NotStageImplementException
from agieval.common.constant import RUNTIME_PARAM_BENCHMARK_ID, RUNTIME_PARAM_BENCHMARK_PATH, RUNTIME_PARAM_USE_CACHE, RUNTIME_PARAM_WORK_DIR, RUNTIME_PARAM_BENCHMARK_CONFIG_FILE, RUNTIME_PARAM_METRICS_NAME
from agieval.entity.global_param import GlobalParam
from agieval.plugin.metrics.base_metrics import BaseMetrics


GLOBAL_PARAM_REF = "#GLOBAL#"

def load_model_api_config() -> dict[str, Any]:
    return dict(
        base_url=os.getenv("API_BASE_URL", ""),
        model=os.getenv("MODEL_NAME", ""),
        api_key=os.getenv("API_KEY", ""),
        score_base_url=os.getenv("SCORE_API_BASE_URL", ""),
        score_model=os.getenv("SCORE_MODEL_NAME", ""),
        score_api_key=os.getenv("SCORE_API_KEY", "")
    )


def find_field_info(plugin_param_class: type[BasePluginParam], all_field_info: dict[type[BasePluginParam], set[str]]) -> set[str]:
    current_all_fields = set(plugin_param_class.model_fields.keys())
    if plugin_param_class in all_field_info:
        return current_all_fields
    
    parent_field_info: dict[type[BasePluginParam], set[str]] = {}
    for base in plugin_param_class.__bases__:
        if not issubclass(base, BasePluginParam):
            continue
        parent_field_info[base] = find_field_info(base, all_field_info)

    current_fields = set(current_all_fields)
    for base, fileds in parent_field_info.items():
        current_fields = current_fields - fileds
    all_field_info[plugin_param_class] = current_fields    
    return current_all_fields


def find_duplicate_fields(plugin_classes: list[type[BasePlugin]]):
    """Find duplicate fields among multiple model classes"""
    all_fields: dict[str, type[BasePluginParam]] = {}
    duplicates: dict[str, list[str]] = {}
    all_field_info: dict[type[BasePluginParam], set[str]] = {}
    
    for plugin_class in plugin_classes:
        find_field_info(plugin_class.get_generic_param_type(), all_field_info)
  
    def get_module_location(plugin_param_class: type[BasePluginParam]) -> str:
        # Get the module and file path where the class is located
        file_path = None
        try:
            file_path = inspect.getsourcefile(plugin_param_class)
        except (ImportError, TypeError):
            pass
        if not file_path:
            file_path = plugin_param_class.__module__
        return file_path

    for plugin_param_class, fields in all_field_info.items():
        for field in fields:
            if field in all_fields:
                if field not in duplicates:
                    duplicates[field] = [f"{all_fields[field].__name__} ({get_module_location(all_fields[field])})"]
                duplicates[field].append(f"{plugin_param_class.__name__} ({get_module_location(plugin_param_class)})")
            else:
                all_fields[field] = plugin_param_class
    return duplicates

def check_duplicate_fields_for_plugins(plugin_classes: list[type[BasePlugin]]):
    duplicates_fields = find_duplicate_fields(plugin_classes)
    repeat_error_msgs = []
    for field, classes in duplicates_fields.items():
        classes_str = "\n".join(["\t" + c for c in classes])
        repeat_error_msgs.append(f"Parameter name {field} is defined repeatedly in the following plugin implementations: \n{classes_str}")
    repeat_error_msg = "\n" + "\n".join(repeat_error_msgs) if repeat_error_msgs else None
    assert not repeat_error_msg, f"\nPlugin parameter names must be globally unique, need to modify parameter names or extract common parameters to parent class definition{repeat_error_msg}"

def replace_global_param_ref(value, global_param: GlobalParam | None):
    if not isinstance(value, str) or not value.startswith(GLOBAL_PARAM_REF) or global_param is None:
        return value
    global_value = getattr(global_param, value.replace(GLOBAL_PARAM_REF, ""), None)  
    return value if global_value is None else global_value

def context_param_update(context_params: ContextParam, runtime_params: ContextParam) -> ContextParam:
    """
    Override fields in context_params with values from runtime_params
    If a field in runtime_params does not exist in context_params, it is ignored
    """
    if context_params is None:
        context_params = {}
    result = copy.deepcopy(context_params)    
    if runtime_params is None:
        return context_params
    
    for key, value in runtime_params.items():
        if key in result:
            result[key] = value
    return result

def context_param_overwrite(context_params: ContextParam, global_param: GlobalParam | None = None, plugin_param: dict = {}) -> ContextParam:
    """
    Convert parameter list to dictionary
    """
    context_params = {} if context_params is None else copy.deepcopy(context_params)
    
    context_dict: ContextParam = {}
    # Filter out empty key-value pairs
    for name, value in context_params.items():
        final_value = replace_global_param_ref(value, global_param)
        if final_value is not None and final_value != '<empty>':
            context_dict[name] = final_value
    if plugin_param is not None:
        context_dict = context_param_update(context_dict, plugin_param)
    return context_dict

def add_runtime_param(context_params: ContextParam, runtime_param_name: str, runtime_param_value: str):
    context_params.update({runtime_param_name: runtime_param_value})

def completeBenchmarkConfig(benchmark_config: BenchmarkConfig, eval_config: EvalConfig) -> BenchmarkConfig:
    plugin_classes: list[type[BasePlugin]] = []
    use_cache = benchmark_config.use_cache
    for flow_stage in benchmark_config.flow_stages:
        if not use_cache:
            # If dataset specifies ignoring cache or previous stage specifies ignoring cache, current stage must ignore cache
            flow_stage.use_cache = False
        if use_cache and not flow_stage.use_cache:
            # If dataset specifies using cache, current stage specifies ignoring cache, subsequent stages must ignore cache
            use_cache = False

        # Load stage_plugin
        PluginFactory.find_plugin(plugin_implement=flow_stage.plugin_implement)
        stage_plugin = PluginFactory[BasePlugin].get_plugin_class_by_name(flow_stage.plugin_implement)
        if not issubclass(stage_plugin, BaseStage):
            raise NotStageImplementException(f"{flow_stage.plugin_implement} is not a BaseStage implementation class")
        plugin_classes.append(stage_plugin)
        stage_param = stage_plugin.get_default_plugin_param()
        
        # Supplement stage_plugin runtime parameters
        context_params = context_param_update(stage_param.model_dump(), flow_stage.context_params)
        add_runtime_param(context_params, RUNTIME_PARAM_BENCHMARK_ID, benchmark_config.benchmark)
        add_runtime_param(context_params, RUNTIME_PARAM_BENCHMARK_PATH, benchmark_config.location_test)
        add_runtime_param(context_params, RUNTIME_PARAM_USE_CACHE, str(flow_stage.use_cache))
        add_runtime_param(context_params, RUNTIME_PARAM_WORK_DIR, eval_config.work_dir)
        context_params = context_param_overwrite(
            context_params=context_params,
            global_param=eval_config.global_param,
            plugin_param=eval_config.plugin_param
        )
        flow_stage.context_params = context_params
        flow_stage.plugin_type = stage_plugin.plugin_type
        if not flow_stage.stage:
            flow_stage.stage = stage_plugin.__name__
            
        
        # Iterate through step_plugin processing
        PluginFactory.find_plugins(flow_stage.plugins)
        plugin_types: dict[PluginType, list[PluginConfig]] = {}
        for plugin in flow_stage.plugins:
            plugin_type = PluginFactory.get_plugin_type_by_name(plugin_name=plugin.plugin_implement)
            if plugin_type not in plugin_types:
                plugin_types[plugin_type] = []
            plugin_types[plugin_type].append(plugin)

        plugin_configs: list[PluginConfig] = []
        for step_plugin_type in stage_plugin.get_steps():
            plugin_configs_by_type = plugin_types.get(step_plugin_type)
            if not plugin_configs_by_type:
                plugin_configs_by_type = [PluginConfig(plugin_type=step_plugin_type, context_params={})]
            
            for plugin_config_by_type in plugin_configs_by_type:
                if plugin_config_by_type.plugin_implement:
                    step_plugin = PluginFactory[BasePlugin].get_plugin_class_by_name(plugin_config_by_type.plugin_implement)
                else:
                    step_plugin = PluginFactory[BasePlugin].get_plugin_class_by_type(step_plugin_type)

                if not issubclass(step_plugin, BaseStep):
                    raise NotStageImplementException(f"{step_plugin.__name__} is not a BaseStep implementation class")
                plugin_classes.append(step_plugin)
                step_param = step_plugin.get_default_plugin_param()

                # Supplement step_plugin runtime parameters
                context_params = context_param_update(step_param.model_dump(), plugin_config_by_type.context_params)
                add_runtime_param(context_params, RUNTIME_PARAM_BENCHMARK_ID, benchmark_config.benchmark)
                add_runtime_param(context_params, RUNTIME_PARAM_BENCHMARK_PATH, benchmark_config.location_test)
                add_runtime_param(context_params, RUNTIME_PARAM_WORK_DIR, eval_config.work_dir)
                if issubclass(step_plugin, BaseMetrics) and not context_params.get(RUNTIME_PARAM_METRICS_NAME):
                    add_runtime_param(context_params, RUNTIME_PARAM_METRICS_NAME, step_plugin.get_metrics_name())
                        
                context_params = context_param_overwrite(
                    context_params=context_params,
                    global_param=eval_config.global_param,
                    plugin_param=eval_config.plugin_param
                )
                plugin_config_by_type.context_params = context_params
                if not plugin_config_by_type.plugin_implement:
                    plugin_config_by_type.plugin_implement = step_plugin.__name__ 
                plugin_configs.append(plugin_config_by_type)

        flow_stage.plugins = plugin_configs

    # Check if plugin parameter names are duplicated
    # TODO: Cache analyzed classes
    check_duplicate_fields_for_plugins(plugin_classes)
    return benchmark_config


def load_benchmark_configs(eval_config: EvalConfig, benchmark_config: str | BenchmarkConfig | list[BenchmarkConfig], flow_config_file: str = "") -> list[BenchmarkConfig]:
    benchmark_configs = _load_benchmark_configs(eval_config, benchmark_config, flow_config_file)
    PluginFactory.clear()
    return benchmark_configs

def _load_benchmark_configs(eval_config: EvalConfig, benchmark_config: str | BenchmarkConfig | list[BenchmarkConfig], flow_config_file: str = "") -> list[BenchmarkConfig]:
    if benchmark_config is None:
        raise FlowConfigParseException("Dataset configuration file not specified")
    
    if eval_config.benchmark_config_template:
        benchmark_configs = load_benchmark_config_template(eval_config.dataset_files, benchmark_config)
    elif isinstance(benchmark_config, BenchmarkConfig):
        benchmark_configs = [benchmark_config]
    elif isinstance(benchmark_config, list):
        benchmark_configs = benchmark_config
    else:
        benchmark_configs = load_benchmark_config_file(benchmark_config)
        
    for benchmark_config_item in benchmark_configs:
        if benchmark_config_item.flow_stages is not None and benchmark_config_item.flow_stages:
            continue
        if benchmark_config_item.flow_config_file:
            benchmark_config_item.flow_stages = load_flow_config(benchmark_config_item.flow_config_file)
            continue
        if flow_config_file:
            benchmark_config_item.flow_stages = load_flow_config(flow_config_file)
        
        raise FlowConfigParseException(f"Dataset {benchmark_config_item.benchmark} did not specify evaluation task flow configuration file")
    
    return [completeBenchmarkConfig(benchmark_config_item, eval_config) for benchmark_config_item in benchmark_configs]
            
def load_benchmark_config_template(dataset_files: str, benchmark_config_template) -> list[BenchmarkConfig]:
    assert isinstance(benchmark_config_template, str) or isinstance(benchmark_config_template, BenchmarkConfig), "Dataset configuration template must be a file or BenchmarkConfig object"
    json_files: list[str] = []

    dataset_dir = dataset_files
    assert os.path.isdir(dataset_files),  "Dataset files must be a directory"
    dataset_location = os.path.join(dataset_files, "_dataset_location.txt")
    if os.path.exists(dataset_location):
        dataset_files = dataset_location

    if os.path.isdir(dataset_files):
        json_files = [path.as_posix() for path in Path(dataset_files).glob('*.json')]
        real_dataset = [(os.path.splitext(os.path.split(json_file)[1])[0], json_file) for json_file in json_files]
    else:
        def parse_json_file(json_file: str):
            json_file = json_file.strip()
            contents = json_file.split(",")
            if len(contents) == 2:
                return contents[1].strip(), os.path.join(dataset_dir, contents[0].strip())
            assert len(contents) == 1, f"Dataset actual address file content format error, required format is [file directory, dataset name], error content: {json_file} "
            return os.path.splitext(os.path.split(contents[0])[1])[0], os.path.join(dataset_dir, json_file)

        with open(dataset_files, "r") as f:
            json_files = f.readlines()
            real_dataset = [parse_json_file(json_file) for json_file in json_files if json_file.strip()]

    assert real_dataset, "Dataset actual address not found, check if the directory specified by dataset_files exists"

    benchmark_configs = load_benchmark_config_file(benchmark_config_template) if isinstance(benchmark_config_template, str) else [benchmark_config_template]
    benchmark_config_template = benchmark_configs[0]
    benchmark_configs = []
    for dataset, json_file in real_dataset:
        real_benchmark_config = copy.deepcopy(benchmark_config_template)
        real_benchmark_config.benchmark = dataset.strip()
        real_benchmark_config.location_test = json_file.strip()
        benchmark_configs.append(real_benchmark_config)
    return benchmark_configs
            
def load_benchmark_config_file(benchmark_config_file: str) -> list[BenchmarkConfig]:
    benchmark_config_dict = {}
    if os.path.isdir(benchmark_config_file):
        benchmark_config_file = os.path.join(benchmark_config_file, RUNTIME_PARAM_BENCHMARK_CONFIG_FILE)
    if os.path.isfile(benchmark_config_file):
        ext = os.path.splitext(benchmark_config_file)[-1]
        if ext == ".json":
            try:
                with open(benchmark_config_file) as f:
                    benchmark_config_dict = json.load(f)
            except Exception as e:
                raise FlowConfigParseException(f"Evaluation task file parsing exception {benchmark_config_file}") from e
    
    if isinstance(benchmark_config_dict, dict):
        benchmark_configs = [BenchmarkConfig.model_validate(benchmark_config_dict)]
    elif isinstance(benchmark_config_dict, list):
        benchmark_configs = [BenchmarkConfig.model_validate(benchmark_config) for benchmark_config in benchmark_config_dict]
    else:
        benchmark_configs = []
    return benchmark_configs


def load_flow_config(flow_config_file: str) -> list[FlowStage]:
    if flow_config_file is None or not flow_config_file:
        raise FlowConfigParseException("Evaluation task flow configuration file not specified")
    
    flow_stages = []
    if os.path.isdir(flow_config_file):
        flow_config_file = os.path.join(flow_config_file, "flow_config.json")
    if os.path.isfile(flow_config_file):
        ext = os.path.splitext(flow_config_file)[-1]
        if ext == ".json":
            try:
                with open(flow_config_file) as f:
                    stages = json.load(f)
                    flow_stages = [FlowStage.model_validate(stage) for stage in stages]    
            except Exception as e:
                raise FlowConfigParseException(f"Evaluation task flow configuration file parsing exception {flow_config_file}") from e
    if not flow_stages:
        raise FlowConfigParseException(f"Evaluation task flow configuration file does not exist {flow_config_file}")
    return flow_stages