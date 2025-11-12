# Plugin System

## Overview

The plugin system is located in [agieval/core/plugin](https://github.com/AGI-Eval-Official/agi-eval/tree/master/agieval/plugin), responsible for plugin definition, registration, loading, and execution. It adopts generic design, providing type-safe plugin interfaces.

## Directory Structure

```bash
agieval/
└── core/
    └── plugin/
        ├── base_plugin.py          # Plugin base class
        ├── base_plugin_param.py    # Plugin parameter base class
        ├── plugin_factory.py       # Plugin factory class
        └── plugins_decorator.py    # Plugin decorators
```

## Plugin Definition

### PluginType
[PluginType](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/flow_config.py) defines all plugin types. Different plugins of the same type can achieve the same goal through their respective strategies, which are concrete implementations of the strategy pattern.

Each plugin needs to determine its plugin type through a plugin decorator, and the plugin factory identifies and loads plugins based on plugin types.


### BasePlugin
[BasePlugin](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin.py) is the base class for all plugins, defining the basic interfaces and behaviors of plugins.

Main features:

- Generic support: Manage plugin custom parameters through generic parameters.
- Automatic configuration validation: Use Pydantic for configuration validation.
- Logging support: Built-in logging functionality.

Plugins are divided into two major categories: `stage plugins` and `step plugins`.

### BaseStage
[BaseStage](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin.py) is the base class for stage plugins, inheriting from [BasePlugin](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin.py), used to manage the main stages of the evaluation process. The core function is to schedule the execution of multiple sub-steps. A stage is defined as an independently runnable functional module, and any combination of stages represents a specific implementation of an evaluation process.

Main features:

- Cache support: Support result caching to avoid repeated computation, providing cache availability check interface.
- Step management: Define the processing steps included in a stage, each step corresponds to a step plugin.

Each step should only define the plugin type, and the specific implementation is determined by the step plugin implementation class configured at runtime.

### BaseStep
[BaseStep](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin.py) is the base class for step plugins, inheriting from [BasePlugin](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin.py), used to implement specific processing steps.

Step plugins cannot be used alone and must exist as sub-components of stage plugins.


## Plugin Parameters

Each plugin must specify a corresponding parameter class to define adjustable hyperparameters during plugin execution.

### BasePluginParam
[BasePluginParam](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin_param.py) inherits from Pydantic's **BaseModel** and is the base class for all plugin parameters, defining common parameters for all plugins and general parameter value handling methods.

- `benchmark_id` Name of the dataset being executed.
- `work_dir` Output directory of this evaluation.

### BaseStagePluginParam
[BaseStagePluginParam](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin_param.py) inherits from [BasePluginParam](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin_param.py) and is the base class for stage plugin parameters.

- `use_cache` Whether to use cache. If partial evaluation data already exists in `work_dir`, it can be used as cache.

### BaseStepPluginParam
[BaseStepPluginParam](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin_param.py) inherits from [BasePluginParam](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin_param.py) and is the base class for step plugin parameters.


## Plugin Decorators
Plugin decorators [plugins_decorator](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/plugins_decorator.py) bind unique plugin types, providing support for plugin factory to identify and load plugins.

**Built-in Decorators**
```python
# Stage plugin decorators
@DataProcessorPlugin
@InferProcessorPlugin
@MetricsProcessorPlugin
@ReportProcessorPlugin

# Step plugin decorators
@DataScenarioPlugin
@DataAdapterPlugin
@DataWindowServicePlugin
@InferLoadModelPlugin
@InferAgentPlugin
@MetricsPlugin
@ReportPlugin
```

## Plugin Factory
Plugin factory [plugin_factory](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/plugin_factory.py) is responsible for plugin loading, caching, and instantiation.

### PluginLoader
Plugin loader, responsible for loading plugin classes and caching loaded plugin classes.

Main functions:

- Plugin Center: Record the package path corresponding to each type of plugin and default plugin implementations.
- Plugin Loading: Search for plugin classes in corresponding package paths based on plugin types, and cache loaded plugin classes to avoid repeated loading.
- Dependency Installation: Automatically install unique dependency packages for loaded plugins.

### PluginFactory
Plugin factory, responsible for instantiating plugin objects based on plugin types and configuration, non-singleton mode, each plugin acquisition will re-instantiate the plugin object.

Main functions:

- Plugin Loading: Load plugin classes through `PluginLoader`.
- Get Plugin: Get plugin classes based on plugin type or plugin name, parse runtime parameters, and instantiate plugin objects.

## Plugin Implementation

### Directory Structure

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

### Data Processing Stage
The data processing stage is responsible for operations such as data preprocessing, cleaning, and transformation. Its main capability is to shield differences between different datasets and provide consistent data processing interfaces. Processing steps are as follows:

- `scenario` Core step, used to load datasets and output unified data format
- `adapter` Optional step, used for data processing and output prompts
- `window_service` Optional step, used in data stage to avoid exceeding model context length


### Inference Processing Stage
The inference processing stage is responsible for processing inference results of each instance. Its main capability is to shield differences between different models and frameworks and provide consistent inference interfaces. Processing steps are as follows:

- `model` Core step, shields model differences, inputs instances and outputs inference results
- `agent` Core step, assembles complete prompts, calls `model` plugin to get inference results

### Metric Calculation Stage
Responsible for calculating metrics for each instance, its main capability is to aggregate multiple metric calculation methods. Processing steps are as follows:

- `metrics` Calculate specific metrics

### Report Generation Stage
Responsible for generating evaluation reports, its main capability is statistical analysis of evaluation results. Processing steps are as follows:

- `report` A statistical analysis method
