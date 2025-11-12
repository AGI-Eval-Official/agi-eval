from typing import TypeVar, cast
from collections.abc import Callable
from agieval.common.logger import log
      
from agieval.core.plugin.base_plugin import BasePlugin
from agieval.entity.flow_config import PluginType



T = TypeVar('T', bound=BasePlugin)  # Used to preserve original type
_plugin_type_to_decorator_name_map: dict[PluginType, str] = {}

# Modify decorator implementation to use inheritance to preserve type relationships
def create_plugin_decorator(plugin_type: PluginType, decorator_name: str) -> Callable[[type[T]], type[T]]:
    """
    Create a plugin decorator that preserves the original type and automatically associates plugin types with decorators

    Args:
        plugin_type: Plugin type
        decorator_name: Decorator name

    Returns:
        A decorator function that returns a new class inheriting from the original class when applied
    """
    def decorator(cls: type[T]) -> type[T]:
        """
        Decorator function that takes a class and returns a new class
        This new class inherits from the original class while adding plugin-related functionality
        """
        # Create a new class that inherits from the original class
        class WrappedPlugin(cls):
            def __init__(self, *args, **kwargs):
                # Call the original class's initialization method
                super().__init__(*args, **kwargs)
                log(f"Plugin {cls.__name__} instantiation completed, context_param={self.context_param.model_dump_json()}")

        # Set the new class's name and module to make it look like the original class
        WrappedPlugin.__name__ = cls.__name__
        WrappedPlugin.__module__ = cls.__module__
        WrappedPlugin.__qualname__ = cls.__qualname__
        WrappedPlugin.__doc__ = cls.__doc__

        # Record decorator information
        WrappedPlugin.plugin_type = plugin_type

        return cast(type[T], WrappedPlugin)

    # Register decorator name and decorator function
    _plugin_type_to_decorator_name_map[plugin_type] = decorator_name
    return decorator


def get_plugin_decorator_name(plugin_type: PluginType) -> str:
    """
    Get the corresponding plugin decorator name based on PluginType

    Args:
        plugin_type: Plugin type

    Returns:
        The corresponding plugin decorator name

    Raises:
        ValueError: If the corresponding plugin decorator name is not found
    """
    if plugin_type not in _plugin_type_to_decorator_name_map:
        raise ValueError(f"Decorator name for plugin type {plugin_type} not found")
    return _plugin_type_to_decorator_name_map[plugin_type]



# Create various plugin decorators
# These decorators will be automatically registered to _plugin_type_to_decorator_name_map
DataProcessorPlugin = create_plugin_decorator(PluginType.STAGE_DATA_PROCESSOR, "DataProcessorPlugin") # Base class DataProcessor
InferProcessorPlugin = create_plugin_decorator(PluginType.STAGE_INFER_PROCESSOR, "InferProcessorPlugin") # Base class InferProcessor
MetricsProcessorPlugin = create_plugin_decorator(PluginType.STAGE_METRICS_PROCESSOR, "MetricsProcessorPlugin") # Base class MetricsProcessor
ReportProcessorPlugin = create_plugin_decorator(PluginType.STAGE_REPORT_PROCESSOR, "ReportProcessorPlugin") # Base class ReportProcessor

DataScenarioPlugin = create_plugin_decorator(PluginType.DATA_SCENARIO, "DataScenarioPlugin") # Base class BaseScenario
DataAdapterPlugin = create_plugin_decorator(PluginType.DATA_ADAPTER, "DataAdapterPlugin") # Base class BaseAdapter
DataWindowServicePlugin = create_plugin_decorator(PluginType.DATA_WINDOW_SERVICE, "DataWindowServicePlugin") # Base class BaseWindowService

InferLoadModelPlugin = create_plugin_decorator(PluginType.INFER_LOAD_MODEL, "InferLoadModelPlugin") # Base class BaseModel
InferAgentPlugin = create_plugin_decorator(PluginType.INFER_AGENT, "InferAgentPlugin") # Base class BaseAgent

MetricsPlugin = create_plugin_decorator(PluginType.METRICS, "MetricsPlugin") # Base class BaseMetrics

ReportPlugin = create_plugin_decorator(PluginType.REPORT, "ReportPlugin") # Base class BaseReport
