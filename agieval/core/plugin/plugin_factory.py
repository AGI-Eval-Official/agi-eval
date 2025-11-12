import ast
import os
import glob
import importlib.util
import copy
import json

from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import sys
from typing import Any, Generic, TypeVar, cast


from agieval.common.logger import log, log_debug, log_error
from agieval.core.plugin.base_plugin import BasePlugin
from agieval.core.plugin.plugins_decorator import get_plugin_decorator_name
from agieval.entity.flow_config import PluginConfig, ContextParam, PluginType


T = TypeVar("T", bound=BasePlugin)

@dataclass
class PluginCenter(Generic[T]):
    base_packages: list[str]
    default_plugin: str
    registry: dict[str, tuple[type[T], str]] = field(default_factory=dict)


class PluginLoader(Generic[T]):

    plugin_centers: dict[PluginType, PluginCenter[T]] = {
        PluginType.STAGE_DATA_PROCESSOR: PluginCenter(["agieval.plugin.stage.data"], "SimpleDataProcessor"),
        PluginType.STAGE_INFER_PROCESSOR: PluginCenter(["agieval.plugin.stage.infer"], "SimpleInferProcessor"),
        PluginType.STAGE_METRICS_PROCESSOR: PluginCenter(["agieval.plugin.stage.metrics"], "SimpleMetricsProcessor"),
        PluginType.STAGE_REPORT_PROCESSOR: PluginCenter(["agieval.plugin.stage.report"], "SimpleReportProcessor"),

        PluginType.DATA_SCENARIO: PluginCenter(["agieval.plugin.scenario"], "GenerationScenario"),
        PluginType.DATA_ADAPTER: PluginCenter(["agieval.plugin.adapter"], "GenerationAdapter"),
        PluginType.DATA_WINDOW_SERVICE: PluginCenter(["agieval.plugin.window_service"], "GenerationWindowService"),

        PluginType.INFER_LOAD_MODEL: PluginCenter(["agieval.plugin.model"], "LiteLLMModel"),
        PluginType.INFER_AGENT: PluginCenter(["agieval.plugin.agent"], "SingleRoundTextAgent"),

        PluginType.METRICS: PluginCenter(["agieval.plugin.metrics"], "QuasiPrefixExactMatchMetrics"),

        PluginType.REPORT: PluginCenter(["agieval.plugin.report"], "VisualizationReport")
    }

    _plugin_file_cache: dict[str, dict[str, dict[str, str]]] = {}
    _module_requirements_cache: dict[str, list[str]] = {}


    @classmethod
    def load_plugin(cls, plugin_name: str = "", plugin_type: PluginType = PluginType.NONE_TYPE) -> tuple[type[T], str]:
        assert plugin_name != "" or plugin_type != PluginType.NONE_TYPE, "Plugin type and plugin implementation class cannot both be empty"

        if plugin_name == "":
            plugin_name = cls.plugin_centers[plugin_type].default_plugin
            
        plugin = None
        location = ""
        for plugin_type_item, plugin_center in cls.plugin_centers.items():
            plugin_type_value = plugin_type_item.value
            if plugin_type is not None and plugin_type != PluginType.NONE_TYPE and plugin_type_item != plugin_type:
                continue
            plugin, location = plugin_center.registry.get(plugin_name, (None, ""))
            if plugin is not None:
                log_debug(f"Plugin search ended, already loaded plugin {plugin_name}, type [{plugin_type_value}], location: {location}")
                break
            
            log_debug(f"Plugin search started, plugin to load {plugin_name}, type [{plugin_type_value}] ...")
            plugin, location = cls._find_plugin(plugin_name, plugin_type_item, plugin_center)
            if plugin:
                log_debug(f"Plugin search ended, loaded plugin {plugin_name}, type [{plugin_type_value}], location: {location}")
            else:
                log_debug(f"Plugin search ended, plugin {plugin_name} not found, type [{plugin_type_value}]")
            if plugin is not None and location is not None:
                plugin_center.registry[plugin_name] = (plugin, location)
                break
        
        assert plugin is not None, f"Plugin {plugin_name} not found"
        return plugin, location


    @classmethod
    def _find_plugin(cls, plugin_name: str, plugin_type: PluginType, plugin_center: PluginCenter) -> tuple[type[T], str] | tuple[None, str]:
        """
        Plugin search method with caching functionality to avoid repeated file scanning
        """
        target_decorator_name = get_plugin_decorator_name(plugin_type)
        result = {}

        # Iterate through all base package paths
        cache_update = False
        for base_package in plugin_center.base_packages:
            # Check if there's already a scan result for this package in cache
            if base_package not in cls._plugin_file_cache:
                # If no cache exists, scan and build cache
                cache_update = True
                cls._plugin_file_cache[base_package] = {}
                file_path = os.path.join(Path(__file__).parent.parent.parent.parent, *base_package.split("."))
                python_files = glob.glob(os.path.join(file_path, "**/*.py"), recursive=True)

                for py_file in python_files:
                    if os.path.basename(py_file) == "__init__.py":
                        continue

                    try:
                        with open(py_file, encoding="utf-8") as f:
                            try:
                                tree = ast.parse(f.read(), filename=str(py_file))
                            except (SyntaxError, UnicodeDecodeError):
                                continue  # Skip files that cannot be parsed

                        # Scan all classes and decorators in the file
                        file_classes: dict[str, str ]= {}
                        # Add file to cache
                        cls._plugin_file_cache[base_package][str(py_file)] = file_classes
                        for node in ast.walk(tree):
                            if not isinstance(node, ast.ClassDef):
                                continue

                            class_name = node.name
                            # Check all decorators of the class
                            for decorator in node.decorator_list:
                                if isinstance(decorator, ast.Name):
                                    decorator_name = decorator.id
                                    file_classes[class_name] = decorator_name
                
                    except Exception as e:
                        log_error(f"Error parsing file {py_file}: {str(e)}")
                
            # Find matching plugin from cache
            for file_path, classes in cls._plugin_file_cache[base_package].items():
                if plugin_name in classes and classes[plugin_name] == target_decorator_name:
                    result[file_path] = base_package
        
        if cache_update:
            log_debug(f"_find_plugin, plugin file cache updated: {cls._plugin_file_cache}")

        file_paths = list(result.keys())
        if not file_paths:
            return None, ""
        assert len(file_paths) == 1, f"Duplicate plugin {plugin_name} found, file paths: {file_paths}"

        file_path = file_paths[0]
        base_package = result[file_path]

        module = cls._load_module_from_path(file_path, base_package)
        # 获取类
        plugin_class = cast(type[T], getattr(module, plugin_name))
        return plugin_class, file_path

    @classmethod
    def _load_module_from_path(cls, file_path: str, base_package: str) -> Any:
        """Load Python module from file path"""
        import sys
        module_name = os.path.basename(file_path).replace('.py', '')
        module_name = f"{base_package}.{module_name}"
        if  module_name in sys.modules:
           return sys.modules[module_name]
        
        cls.install_requirements(module_name)
        spec = importlib.util.spec_from_file_location(f"{base_package}.{module_name}", file_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    
    @classmethod
    def install_requirements(cls, module_name):
        if not cls._module_requirements_cache:
            with open("agieval/plugin/requirements.json", "r") as f:
                cls._module_requirements_cache = json.load(f)
        
        if module_name not in cls._module_requirements_cache:
            return

        dependencies = cls._module_requirements_cache[module_name]
        if not dependencies:
            return
        dependencies_str = "\n".join(dependencies)
        log(f"Start installing dependency packages, module_name={module_name}, dependencies:\n{dependencies_str}")
        # Install dependencies via pip
        cls.run_install_command(dependencies)
    

    @classmethod
    def run_install_command(cls, dependencies: list[str]):
        cmd = [
            sys.executable, "-m", "pip", "install", *dependencies
        ]
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for line in process.stdout:
            log(line.strip())
        process.wait()
        if process.returncode != 0:
            raise Exception(f"Error occurred while installing dependency packages: {line}")
        

class PluginFactory(Generic[T]):
    plugin_names_dict: dict[PluginType, list[str]] = {}
    plugin_dict: dict[str, type[T]] = {}
    plugin_param_dict: dict[str, dict] = {}
    plugin_location_dict: dict[str, str] = {}

    @classmethod
    def clear(cls):
        cls.plugin_names_dict = {}
        cls.plugin_dict = {}
        cls.plugin_param_dict = {}

    @classmethod
    def find_plugin(cls, plugin_implement: str = "", plugin_type: PluginType = PluginType.NONE_TYPE, context_params: ContextParam = {}) -> PluginType:
        plugin_configs = [PluginConfig(plugin_type=plugin_type, plugin_implement=plugin_implement, context_params=context_params)]
        plugin_configs = cls.find_plugins(plugin_configs)
        return plugin_configs[0].plugin_type

    @classmethod
    def find_plugins(cls, plugin_config_list: list[PluginConfig]) -> list[PluginConfig]:
        
        if plugin_config_list is None:
            plugin_config_list = []
        
        log_debug(f"Initializing plugin instance factory... Plugin configuration: {json.dumps([plugin_config.model_dump() for plugin_config in plugin_config_list])}")
    
        for plugin_config in plugin_config_list:
            plugin, location = PluginLoader[T].load_plugin(
                plugin_name=plugin_config.plugin_implement,
                plugin_type=plugin_config.plugin_type
            )
            plugin_name = plugin.__name__
            if plugin_name not in cls.plugin_dict:
                cls.plugin_dict[plugin_name] = plugin
                if plugin.plugin_type not in cls.plugin_names_dict:
                    cls.plugin_names_dict[plugin.plugin_type] = [plugin_name]
                else:
                    cls.plugin_names_dict[plugin.plugin_type].append(plugin_name)

            cls.plugin_param_dict[plugin_name] = plugin_config.context_params
            cls.plugin_location_dict[plugin_name] = location
            plugin_config.plugin_type = plugin.plugin_type

        log_debug("Plugin instance factory initialization completed")
        return plugin_config_list

    @classmethod
    def get_plugin_location_by_name(cls, plugin_name: str) -> str:
        location =  cls.plugin_location_dict.get(plugin_name, "")
        if not location:
            cls.find_plugin(plugin_implement=plugin_name)
            location = cls.plugin_location_dict.get(plugin_name, "")
        return location

    @classmethod
    def get_plugin_by_type(cls, plugin_type: PluginType, runtime_param: ContextParam = {}) -> T:
        plugin_names = cls.plugin_names_dict.get(plugin_type)
        if plugin_names is None:
            cls.find_plugin(plugin_type=plugin_type)
            plugin_names = cls.plugin_names_dict.get(plugin_type)
        assert plugin_names is not None, f"Plugin type {plugin_type} has no default plugin implementation configured"
        return cls.get_plugin_by_name(plugin_names[0], runtime_param=runtime_param)
        
    
    @classmethod
    def get_plugins_by_type(cls, plugin_type: PluginType, runtime_param: ContextParam = {}) -> list[T]:
        plugin_names = cls.plugin_names_dict.get(plugin_type)
        if plugin_names is None:
            cls.find_plugin(plugin_type=plugin_type)
            plugin_names = cls.plugin_names_dict.get(plugin_type)
        assert plugin_names is not None, f"Plugin type {plugin_type} has no default plugin implementation configured"
        return [
            cls.get_plugin_by_name(plugin_name, runtime_param=runtime_param) 
            for plugin_name in plugin_names
        ]

    @classmethod
    def get_plugin_by_name(cls, plugin_name: str, runtime_param: ContextParam = {}) -> T:
        plugin = cls.get_plugin_class_by_name(plugin_name)
        plugin_context_param = cls.plugin_param_dict.get(plugin_name, {})
        plugin = plugin(
            cls._parse_context_param(
                context_params=plugin_context_param, 
                runtime_param=runtime_param
            )
        )
        if runtime_param is not None and runtime_param:
            log_debug(f"Plugin {plugin_name} updated runtime_param to: {runtime_param}")
        return plugin
    
    @classmethod
    def get_plugin_class_by_type(cls, plugin_type: PluginType) -> type[T]:
        plugin_names = cls.plugin_names_dict.get(plugin_type)
        if plugin_names is None:
            cls.find_plugin(plugin_type=plugin_type)
            plugin_names = cls.plugin_names_dict.get(plugin_type)
        assert plugin_names is not None, f"Plugin type {plugin_type} has no default plugin implementation configured"
        return cls.get_plugin_class_by_name(plugin_names[0])

    @classmethod
    def get_plugin_class_by_name(cls, plugin_name: str) -> type[T]:
        plugin = cls.plugin_dict.get(plugin_name)
        if plugin is None:
            cls.find_plugin(plugin_implement=plugin_name)
            plugin = cls.plugin_dict.get(plugin_name)
        if plugin is None:
            log_error(f"Plugin {plugin_name} not found")
            raise Exception(f"Plugin {plugin_name} not found")
        return plugin
    
    @classmethod
    def get_plugin_type_by_name(cls, plugin_name: str) -> PluginType:
        plugin = cls.get_plugin_class_by_name(plugin_name)
        return plugin.plugin_type



    
    @staticmethod
    def _parse_context_param(context_params: ContextParam, runtime_param: ContextParam = {}) -> ContextParam:
        """
        Convert parameter list to dictionary
        """
        context_params = {} if context_params is None else copy.deepcopy(context_params)
        runtime_param = copy.deepcopy(runtime_param)
        context_params.update(runtime_param)
        return context_params


