# Plugin Development Guide

## Overview
If you need to adapt new public datasets or custom datasets, or have custom evaluation metric calculation requirements, you need to customize and implement corresponding plugins to support them. This section will detail how to implement a complete plugin from scratch.

## Directory Structure

```bash
agieval/
└── plugin/              # Plugin implementations
    ├── stage/           # Stage plugins
    │   ├── data/        # Data processing stage
    │   ├── infer/       # Inference processing stage
    │   ├── metrics/     # Metric calculation stage
    │   └── report/      # Report generation stage
    ├── scenario/        # Data processing - Scenario plugins
    ├── adapter/         # Data processing - Adapter plugins
    ├── model/           # Inference processing - Model plugins
    ├── agent/           # Inference processing - Agent plugins
    ├── metrics/         # Metric plugins
    ├── report/          # Report plugins
    └── window_service/  # Data processing - Window service plugins
```

## Step Plugins
First, you need to clarify whether you are developing `stage plugins` or `step plugins`. Generally, you only need to develop `step plugins` to implement specific functions such as data format conversion, model calls, metric calculations, etc.

### Add Step Type
First, determine whether the built-in step plugins of the framework can meet your requirements. If the function to be implemented is within the capability coverage of built-in steps, you can directly go to the next step [Add Step Plugin](#add-step-plugin). Otherwise, you can define a new step type as follows, and then add step plugins.

1. `Define Plugin Type` Add new plugin type enumeration in [PluginType](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/flow_config.py).
```python
class PluginType(str, Enum):
    ...
    # Add new plugin type
    CUSTOM = "custom"
```

2. `Define Parameter Class` Add new parameter base class in [step_param](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/plugin_param/step_param.py)
```python
class BaseCustomPluginParam(BaseStepPluginParam):  # Must inherit from step plugin parameter base class BaseStepPluginParam
    pass  # Define parameter fields
```

3. `Define Step Plugin Base Class` Add new type plugin package path in [agieval/plugin](https://github.com/AGI-Eval-Official/agi-eval/tree/master/agieval/plugin), then define step plugin base class.
```python
# Add plugin file under package path agieval/plugin/custom  base_custom.py

from abc import abstractmethod
from typing import TypeVar
from agieval.core.plugin.base_plugin import BaseStep
from agieval.entity.plugin_param.step_param import BaseCustomPluginParam

T = TypeVar('T', bound=BaseCustomPluginParam)  # Define parameter generic
class BaseCustom(BaseStep[T]):   # Must inherit from step plugin base class BaseStep

    @abstractmethod    # Must implement run method, input and output parameters can be customized
    def run(self):
        pass
```

4. `Add Plugin Decorator` Add new plugin decorator in [plugins_decorator](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/plugins_decorator.py).
```python
CustomPlugin = create_plugin_decorator(PluginType.CUSTOM, "CustomPlugin") # Base class BaseCustom, record the base class of plugin type
```



### Add Step Plugin
The process of defining a step plugin is very simple:

1. Check [plugins_decorator.py](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/plugins_decorator.py) file to determine the plugin decorator according to the plugin type to be developed.
2. Inherit the step plugin base class corresponding to the step type.
3. Specify the parameter class of the step plugin (can be newly added).

```python
# Define plugin parameter class (optional)
class BaseCustomParam(BaseCustomPluginParam):
    param: str = Field(default="", description="Parameter description")

# Define step plugin
@CustomPlugin   # Must use plugin decorator
class DummyModel(BaseCustom[BaseCustomParam]):  # Inherit from Custom type step plugin base class

    def run(self):  # Implement run method
        pass
```


## Stage Plugins
> Stage plugins and step plugins are essentially the same, just different base classes need to be inherited.

The capability of stage plugins is implemented by combining multiple step plugins. Therefore, you first need to clarify the specific execution steps, then develop step plugins according to [Step Plugins](#step-plugins), and finally combine step plugins into stage plugins.

### Add Stage Type
The development process is consistent with [Add Step Type](#add-step-type), just need to change the inherited base class.

- `Parameter Class and Decorator` Need to add parameter base class in [stage_param](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/plugin_param/stage_param.py)
```python
class CustomProcessorPluginParam(BaseStagePluginParam):  # Must inherit from stage plugin parameter base class BaseStagePluginParam
    pass  # Define parameter fields

# Add decorator
CustomProcessorPlugin = create_plugin_decorator(PluginType.CUSTOM, "CustomProcessorPlugin")
```

- `Stage Plugin Base Class` Add stage plugin package path in [agieval/plugin/stage](https://github.com/AGI-Eval-Official/agi-eval/tree/master/agieval/plugin/stage), then define stage plugin base class.
```python
T = TypeVar('T', bound=CustomProcessorPluginParam)
class CustomProcessor(BaseStage[T]):
    # Must implement cache_is_available method to determine if cached data is available
    def cache_is_available(self) -> bool:
        return False

    # Must implement get_steps method to return the collection of processing step types for this stage
    @staticmethod
    def get_steps() -> List[PluginType]:
        return [PluginType.CUSTOM]
```

### Add Stage Plugin
```python
# Define plugin parameter class (optional）
class CustomProcessorParam(BaseCustomPluginParam):
    param: str = Field(default="", description="Parameter description")

@CustomProcessorPlugin
class SimpleCustomProcessor(CustomProcessor[CustomProcessorParam]):

    # Must implement process method for process function development
    def process(self, plugin_list: List[PluginConfig], eval_config: EvalConfig):
        pass
        # You can refer to built-in plugin implementations and use PluginFactory to get step plugin instances
