# Configuration Management

## Overview
The configuration management system of the AGI-Eval framework is responsible for parsing and validating configuration files, handling the merging and overriding of multi-layer configurations. The configuration management module supports flexible parameter passing and dynamic configuration rendering, providing powerful configuration capabilities for the framework. This section will detail the usage of configuration files.

Configuration files are generally divided into two parts:

- `Task Configuration` Startup parameters for evaluation tasks, specified at runtime.
- `Dataset Configuration` Defines the evaluation process of datasets, bound to datasets.


## Task Configuration
Task configuration is actually the startup parameters of evaluation tasks. Various parameter values are specified in the startup command. The framework will parse the parameters into [EvalConfig](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/eval_config.py) objects and serialize them to the evaluation result directory.

The `EvalConfig` data structure is as follows
```python
class EvalConfig(BaseModel):

    debug: bool = Field(default=False)
    runner: RunnerType
    benchmark_config_template: bool = Field(default=False)
    dataset_files: str = Field(default="")
    benchmark_config: str = Field(default="")
    flow_config_file: str = Field(default="")
    work_dir: str
    data_parallel: int = Field(default=1)

    global_param: GlobalParam = Field(default_factory=GlobalParam)
    plugin_param: dict = Field(default_factory=dict)
```

### Parameter Introduction

| Field Name | Type | Required | Default | Description |
|------------|------|----------|---------|-------------|
| `debug` | bool | No | False | Enable debug mode |
| `runner` | string | No | dummy | Evaluation executor type |
| `benchmark_config_template` | boolean | No | False | Whether dataset configuration is used as template |
| `dataset_files` | string | No | "" | Data index file of dataset |
| `benchmark_config` | string | Yes |  | Dataset configuration file |
| `flow_config_file` | string | No | "" | Evaluation process of dataset, overrides the flow_stages configuration of `benchmark_config` |
| `work_dir` | string | Yes |  | Evaluation result output directory |
| `data_parallel` | int | No | 1 | Number of dataset parallelism |
| `global_param` | string | No | "" | Global parameters, overriding default parameters in dataset configuration |
| `plugin_param` | string | No | "" | Plugin parameters, overriding default parameters in dataset configuration |

### Detailed Description {#eval_config_detail}
#### debug
Enable debug mode, default is False, enable debug mode through the `--debug` parameter

#### runner
Evaluation executor type, supports the following types:

- `dummy` Default executor, will not start actual evaluation tasks, only validates dataset configuration, parses `global_param` and `plugin_param` runtime parameters and overrides dataset configuration, finally assembles complete dataset configuration file and outputs it to the evaluation result directory.
- `local` Single machine executor, starts only one main process to execute evaluation tasks.
- `data_parallel` Data parallel executor, starts corresponding processes to execute evaluation tasks in parallel according to the minimum value of `data_parallel` and the number of datasets.

#### benchmark_config
Specify the path of dataset configuration file. If the specified path is a directory, load the `benchmark_config.json` file in the directory. The file content example is as follows. For field definition description, refer to [Dataset Configuration](#dataset-configuration).

Requires a relative path based on the project root directory.

<details><summary>File Content Example</summary>

```json
[
    {
        "benchmark": "test_example_1",
        "location_test": "example/dataset/test/test_1.json",
        "flow_config_file": "",
        "use_cache": false,
        "flow_stages":
        [
            {
                "plugin_implement": "SimpleDataProcessor",
                "context_params":
                {},
                "plugins":
                [
                    {
                        "plugin_implement": "MultipleChoiceScenario",
                        "context_params":
                        {}
                    }
                ]
            },
            {
                "plugin_implement": "SimpleInferProcessor",
                "context_params":
                {},
                "plugins":
                [
                    {
                        "plugin_implement": "LiteLLMModel",
                        "context_params":
                        {}
                    },
                    {
                        "plugin_implement": "SingleRoundTextAgent",
                        "context_params":
                        {}
                    }
                ]
            },
            {
                "plugin_implement": "SimpleMetricsProcessor",
                "context_params":
                {},
                "plugins":
                [
                    {
                        "plugin_implement": "QuasiPrefixExactMatchMetrics",
                        "context_params":
                        {}
                    }
                ]
            }
        ]
    }
]
```

</details>

#### Dataset Configuration Template
The public datasets adapted by the framework contain multiple sub-dataset categories. The framework will treat sub-datasets as actual evaluation datasets and require each dataset to be bound to a dataset configuration file. Therefore, dataset configuration templates can be bound to public datasets. During actual evaluation, the framework will generate actual dataset configuration files based on the template.

- `benchmark_config_template` Enable dataset configuration template by setting to True
- `dataset_files` Specify the dataset file index, which determines the actual list of datasets to be executed. If the specified path is a directory, load the `_dataset_location.txt` file in the directory. Requires a relative path based on the project root directory.
- `benchmark_config` Specify the path of dataset configuration file, but will only read the first dataset configuration as a template.

#### flow_config_file
Specify the path of dataset evaluation process configuration file. The file content example is as follows. For field description, refer to [Evaluation Process Configuration](#FlowStage). If a dataset does not configure evaluation process, this evaluation process configuration will be used. Generally, this parameter does not need to be specified, and evaluation processes should be specified in dataset configuration.

Requires a relative path based on the project root directory.

<details><summary>File Content Example</summary>

```json
[
    {
        "plugin_implement": "SimpleDataProcessor",
        "context_params":
        {},
        "plugins":
        [
            {
                "plugin_implement": "MultipleChoiceScenario",
                "context_params":
                {}
            }
        ]
    },
    {
        "plugin_implement": "SimpleInferProcessor",
        "context_params":
        {},
        "plugins":
        [
            {
                "plugin_implement": "LiteLLMModel",
                "context_params":
                {}
            },
            {
                "plugin_implement": "SingleRoundTextAgent",
                "context_params":
                {}
            }
        ]
    },
    {
        "plugin_implement": "SimpleMetricsProcessor",
        "context_params":
        {},
        "plugins":
        [
            {
                "plugin_implement": "QuasiPrefixExactMatchMetrics",
                "context_params":
                {}
            }
        ]
    }
]
```

</details>

#### work_dir
Specify the evaluation result output directory.

Can be an absolute path. If it is a relative path, it requires a relative path based on the project root directory.

#### data_parallel
Specify the number of dataset parallelism, only takes effect when `runner` is set to `data_parallel`.

#### global_param
Specify runtime global parameters, overriding default parameters. The complete parameter set can be found in [Global Parameters](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/global_param.py), currently empty implementation.

Parameter assignment method is --global_param k1=v1 k2=v2 ...

#### plugin_param
Specify runtime plugin parameters, overriding default parameters in dataset configuration. The complete parameter set can be found in the specific definition of each plugin.

Parameter assignment method is --plugin_param k1=v1 k2=v2 ...


## Dataset Configuration
Dataset configuration defines the evaluation process of a dataset, bound to the dataset. The framework will parse the parameters into [BenchmarkConfig](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/flow_config.py) lists and serialize them to the evaluation result directory.

### BenchmarkConfig
`BenchmarkConfig` is the complete data structure of dataset configuration.

```python
class BenchmarkConfig(BaseModel):
    benchmark: str
    location_test: str
    flow_stages: list[FlowStage] = Field(default=[])
    flow_config_file: str = Field(default="")
    use_cache: bool = Field(default=True)
```

#### Field Description
| Field Name | Type | Required | Default | Description |
|------------|------|----------|---------|-------------|
| `benchmark` | string | Yes |  | Dataset name |
| `location_test` | string | Yes |  | Dataset file address |
| `flow_stages` | list[FlowStage] | No | [] | Dataset evaluation process |
| `flow_config_file` | string | No | "" | Dataset evaluation process configuration file |
| `use_cache` | bool | No | True | Whether to use cache |

#### Evaluation Process Configuration Description

- `flow_config_file` If multiple datasets need to reuse the same evaluation process, the configuration can be written in an independent file and reused through this field.
- `flow_stages` Evaluation process configuration. If not assigned, use the content of `flow_config_file` file.

#### Simplest Configuration Example

```json
{
    "benchmark": "test",
    "location_test": "datasets/test/example.json",
    "use_cache": false,
    "flow_config_file": "flow_config.json",
    "flow_stages": []
}
```

### FlowStage {#FlowStage}
`FlowStage` is the complete data structure of one stage in the dataset evaluation process.

```python
class FlowStage(BaseModel):
    stage: str = Field(default="")
    plugin_type: PluginType = Field(default=PluginType.NONE_TYPE)
    plugin_implement: str
    context_params: ContextParam = Field(default_factory=dict)
    plugins: list[PluginConfig] = Field(default_factory=list)
    use_cache: bool = Field(default=True)
```

#### Field Description
| Field Name | Type | Required | Default | Description |
|------------|------|----------|---------|-------------|
| `stage` | string | No | "" | Stage name |
| `plugin_type` | string | No | NONE_TYPE | Stage plugin type |
| `plugin_implement` | string | Yes |  | Stage plugin implementation class name |
| `context_params` | dict | No | {} | Set stage plugin parameter values |
| `plugins` | list[PluginConfig] | No | [] | Set step plugin implementation |
| `use_cache` | bool | No | True | Whether to use cache |

#### Detailed Description {#flow_stage_detail}

- `stage` The stage name is used for display in evaluation visualization reports. Generally, it can be left unfilled and will default to the current stage plugin implementation class name.
- `plugin_type` Plugin type, generally does not need to be filled, automatically filled with value based on stage plugin implementation class.
- `plugin_implement` Core field, required, specifies the current stage implementation class, determines what kind of evaluation process it is.
- `context_params` Optional field, `plugin_implement` determines what parameters exist. Through this field, each parameter can be assigned a value, which will override the default value given in the plugin definition.
> **Note** Parameters specified at runtime through [plugin_param](#plugin_param) have the highest priority and will override the values set by this field.
- `plugins` Override step plugin implementation classes. Optional steps have been defined by `plugin_implement`. Unspecified override plugins will use the default implementation. Taking [SimpleDataProcessor](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/plugin/stage/data/data_processor.py) data loading stage as an example, it consists of three step plugins. The default implementation classes of each step can refer to [PluginLoader](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/plugin_factory.py).

#### Simplest Configuration Example
```json
[
    {
        "plugin_implement": "SimpleDataProcessor",
        "context_params":
        {},
        "plugins":
        []
    }
]
```


### PluginConfig
`PluginConfig` is the complete data structure of a specific step in one stage of the dataset evaluation process.
```python
class PluginConfig(BaseModel):
    plugin_implement: str = Field(default="")
    plugin_type: PluginType = Field(default=PluginType.NONE_TYPE)
    context_params: ContextParam = Field(default_factory=dict)
```
#### Field Description
| Field Name | Type | Required | Default | Description |
|------------|------|----------|---------|-------------|
| `plugin_implement` | string | Yes |  | Step plugin implementation class name |
| `plugin_type` | string | No | NONE_TYPE | Step plugin type |
| `context_params` | dict | No | {} | Set step plugin parameter values |

#### Detailed Description {#plugin_config_detail}
refer to [Detailed Description](#flow_stage_detail) in the stage plugin configuration `FlowStage`

#### Simplest Configuration Example
```json
{
    "plugin_implement": "MultiChoiceScenario",
    "context_params":
    {}
}
```

## Configuration Parser
The main code of the parser is in the [load_benchmark_configs](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/common/param_utils.py) method. The main function is to generate complete dataset configuration [BenchmarkConfig](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/flow_config.py) based on task configuration [EvalConfig](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/eval_config.py).

### Configuration Loading
First, dataset configuration needs to be converted to [BenchmarkConfig](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/flow_config.py) objects. Currently, the following methods of specifying dataset configuration are supported:

`agieval start` command startup:

- `Default`: By default, load the variable `benchmark_config_template` in the [config.py](../common_dataset.md#configpy) script, i.e., the `BenchmarkConfig` object.
- `benchmark_config` parameter: If this parameter is specified, read the file content and convert it to `BenchmarkConfig` object through `BenchmarkConfig.model_validate` method.

`run.py` script startup:

- `benchmark_config` parameter: Same as above.

### Template Parsing
If the parameter `benchmark_config_template` is specified, the `BenchmarkConfig` object loaded in the previous step will be used as the dataset configuration template.

- Parse all dataset files to be executed according to the `dataset_files` parameter. Each file serves as the smallest execution unit, i.e., dataset.
- Copy the configuration template object, modify the dataset name and file address, and generate the configuration file for each dataset.

### Parameter Overriding
Each plugin implementation class needs to define the hyperparameters required for its execution. This parameter can be assigned values at the following three levels:

- `Plugin Default Value`, The parameter definition needs to set its default value. For example, set the default value of `base_url` parameter to empty string:

    ```python
    base_url: str = Field(default="", description="Model URL")
    ```

- `Dataset Configuration`, In the dataset configuration file, each plugin implementation class can set its parameter values through the `context_params` field.

    ```json
    {
        "plugin_implement": "LiteLLMModel",
        "context_params":
        {
            "base_url": "http://your-api-endpoint"
        }
    }
    ```

- `Runtime Parameters`, When starting evaluation tasks, the runtime value of each parameter can be set through the `--plugin_param` field.

    ```bash
    --plugin_param base_url=http://your-api-endpoint
    ```


> **Parameter Priority**: Runtime Parameters > Dataset Configuration > Plugin Default Value


## Complete Configuration Example
<details>
<summary>Example</summary>

```json
[
    {
        "benchmark": "test_example_1",
        "location_test": "example/dataset/test/test_1.json",
        "flow_stages": [
            {
                "stage": "SimpleDataProcessor",
                "plugin_type": "stage_data_processor",
                "plugin_implement": "SimpleDataProcessor",
                "context_params": {
                    "benchmark_id": "test_example_1",
                    "work_dir": "result/test",
                    "use_cache": "False",
                    "benchmark_path": "example/dataset/test/test_1.json"
                },
                "plugins": [
                    {
                        "plugin_implement": "MultiChoiceScenario",
                        "plugin_type": "scenario",
                        "context_params": {
                            "benchmark_id": "test_example_1",
                            "work_dir": "result/test",
                            "benchmark_path": "example/dataset/test/test_1.json"
                        }
                    },
                    {
                        "plugin_implement": "MultiChoiceAdapter",
                        "plugin_type": "adapter",
                        "context_params": {
                            "benchmark_id": "test_example_1",
                            "work_dir": "result/test",
                            "max_new_tokens": 4096,
                            "temperature": 0.7,
                            "top_p": 0.95,
                            "top_k": 0,
                            "repeat_penalty": 1,
                            "presence_penalty": 0,
                            "repetition_penalty": 1.0,
                            "benchmark_path": "example/dataset/test/test_1.json"
                        }
                    },
                    {
                        "plugin_implement": "DummyWindowService",
                        "plugin_type": "window_service",
                        "context_params": {
                            "benchmark_id": "test_example_1",
                            "work_dir": "result/test",
                            "benchmark_path": "example/dataset/test/test_1.json"
                        }
                    }
                ],
                "use_cache": false
            },
            {
                "stage": "SimpleInferProcessor",
                "plugin_type": "stage_infer_processor",
                "plugin_implement": "SimpleInferProcessor",
                "context_params": {
                    "benchmark_id": "test_example_1",
                    "work_dir": "result/test",
                    "use_cache": "False",
                    "concurrency": 10,
                    "cache_update_interval": 10,
                    "cache_update_time_interval": 30,
                    "benchmark_path": "example/dataset/test/test_1.json"
                },
                "plugins": [
                    {
                        "plugin_implement": "LiteLLMModel",
                        "plugin_type": "load_model",
                        "context_params": {
                            "benchmark_id": "test_example_1",
                            "work_dir": "result/test",
                            "model": "your-model-name",
                            "base_url": "http://your-api-endpoint",
                            "api_key": "your-api-key",
                            "retry_time": 10,
                            "retry_time_interval": 10,
                            "benchmark_path": "example/dataset/test/test_1.json"
                        }
                    },
                    {
                        "plugin_implement": "SingleRoundTextAgent",
                        "plugin_type": "agent",
                        "context_params": {
                            "benchmark_id": "test_example_1",
                            "work_dir": "result/test",
                            "disable_cache": false,
                            "benchmark_path": "example/dataset/test/test_1.json"
                        }
                    }
                ],
                "use_cache": false
            },
            {
                "stage": "SimpleMetricsProcessor",
                "plugin_type": "stage_metrics_processor",
                "plugin_implement": "SimpleMetricsProcessor",
                "context_params": {
                    "benchmark_id": "test_example_1",
                    "work_dir": "result/test",
                    "use_cache": "False",
                    "benchmark_path": "example/dataset/test/test_1.json"
                },
                "plugins": [
                    {
                        "plugin_implement": "QuasiPrefixExactMatchMetrics",
                        "plugin_type": "metrics",
                        "context_params": {
                            "benchmark_id": "test_example_1",
                            "work_dir": "result/test",
                            "metrics_name": "Accuracy",
                            "benchmark_path": "example/dataset/test/test_1.json"
                        }
                    }
                ],
                "use_cache": false
            },
            {
                "stage": "SimpleReportProcessor",
                "plugin_type": "stage_report_processor",
                "plugin_implement": "SimpleReportProcessor",
                "context_params": {
                    "benchmark_id": "test_example_1",
                    "work_dir": "result/test",
                    "use_cache": "False",
                    "benchmark_path": "example/dataset/test/test_1.json"
                },
                "plugins": [
                    {
                        "plugin_implement": "VisualizationReport",
                        "plugin_type": "report",
                        "context_params": {
                            "benchmark_id": "test_example_1",
                            "work_dir": "result/test",
                            "benchmark_path": "example/dataset/test/test_1.json"
                        }
                    }
                ],
                "use_cache": false
            }
        ],
        "flow_config_file": "example/flow_config/default_flow.json",
        "use_cache": false
    }
]
```

</details>
