# 配置管理

## 概述
agieval 框架的配置管理系统负责解析和验证配置文件，处理多层配置的合并和覆盖，配置管理模块支持灵活的参数传递和动态配置渲染，为框架提供了强大的配置能力。本节将详细介绍配置文件的使用方式

配置文件整体上分为两部分：

- `任务配置` 评测任务的启动参数，运行时指定。
- `数据集配置` 定义数据集的评测流程，绑定在数据集上。


## 任务配置
任务配置实际上就是评测任务的启动参数，在启动命令中指定各项参数值，框架会将参数解析为 [EvalConfig](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/eval_config.py) 对象并序列化输出到评测结果目录中。

`EvalConfig` 数据结构如下
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

### 参数简介

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|------|------|
| `debug` | bool | 否 | False | 开启debug模式 |
| `runner` | string | 否 | dummy | 评测执行器类型 |
| `benchmark_config_template` | boolean | 否 | False | 数据集配置是否作为模板 |
| `dataset_files` | string | 否 | "" | 数据集的数据索引文件 |
| `benchmark_config` | string | 是 |  | 数据集配置文件 |
| `flow_config_file` | string | 否 | "" | 数据集的评测流程，覆盖 `benchmark_config` 的flow_stages配置 |
| `work_dir` | string | 是 |  | 评测结果输出目录 |
| `data_parallel` | int | 否 | 1 | 数据集并行数 |
| `global_param` | string | 否 | "" | 全局参数，覆盖数据集配置中的默认参数 |
| `plugin_param` | string | 否 | "" | 插件参数，覆盖数据集配置中的默认参数 |

### 详细说明 {#eval_config_detail}
#### debug
开启debug模式，默认为False， 通过 `--debug` 参数开启debug模式

#### runner
评测执行器类型，支持以下类型：

- `dummy` 默认执行器，不会启动实际的评测任务，仅校验数据集配置，解析`global_param`、`plugin_param`运行时参数并覆盖数据集配置，最终组装完整的数据集配置文件输出到评测集结果目录中。
- `local` 单机执行器，只启动一个主进程执行评测任务。
- `data_parallel` 数据并行执行器，根据`data_parallel`和数据集数量的最小值启动相应的进程并行执行评测任务。

#### benchmark_config
指定数据集配置文件路径，如果指定路径是一个目录则加载目录下的 `benchmark_config.json` 文件，文件内容示例如下，字段定义说明查看 [数据集配置](#数据集配置)。

要求基于项目根目录的相对路径。

<details><summary>文件内容示例</summary>

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

#### 数据集配置模板
框架已适配的公开数据集是包含了多个子数据集类别的，框架会将子数据集作为实际评测的数据集同时要求每个数据集必须绑定一个数据集配置文件，所以可以在公开数据集上绑定数据集配置模板，实际评测时框架会基于模板生成实际数据集配置文件。

- `benchmark_config_template` 通过设置为True开启数据集配置模板
- `dataset_files` 指定数据集文件索引，这个文件决定了实际要执行的数据集列表。如果指定路径是一个目录则加载目录下的 `_dataset_location.txt` 文件，要求基于项目根目录的相对路径。
- `benchmark_config` 指定数据集配置文件路径，但是只会读取首个数据集配置作为模板使用。

#### flow_config_file
指定数据集的评测流程配置文件路径，文件内容示例如下，字段说明查看 [评测流程配置](#FlowStage)，如果某个数据集没有配置评测流程，则使用这个评测流程配置。一般这个参数不需要指定，数据集配置中都应该指定评测流程。

要求基于项目根目录的相对路径。

<details><summary>文件内容示例</summary>

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
指定评测结果输出目录。

可以是绝对路径，如果是相对路径则要求基于项目根目录的相对路径。

#### data_parallel
指定数据集并行数，仅在 `runner` 设置为 `data_parallel` 时才生效。

#### global_param
指定运行时的全局参数，覆盖默认参数，参数全集见 [全局参数](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/global_param.py)，当前为空实现。

参数赋值方式为 --global_param k1=v1 k2=v2 ...

#### plugin_param
指定运行时的插件参数，覆盖数据集配置中的默认参数，参数全集见每个插件的具体定义。

参数赋值方式为 --plugin_param k1=v1 k2=v2 ...


## 数据集配置
数据集配置定义了一个数据集评测的流程，绑定在数据集上。框架会将参数解析为 [BenchmarkConfig](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/flow_config.py) 列表并序列化输出到评测结果目录中。

### BenchmarkConfig
`BenchmarkConfig` 是数据集配置的完整数据结构。

```python
class BenchmarkConfig(BaseModel):
    benchmark: str
    location_test: str
    flow_stages: list[FlowStage] = Field(default=[])
    flow_config_file: str = Field(default="")
    use_cache: bool = Field(default=True)
```

#### 字段说明
| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|------|------|
| `benchmark` | string | 是 |  | 数据集名字 |
| `location_test` | string | 是 |  | 数据集文件地址 |
| `flow_stages` | list[FlowStage] | 否 | [] | 数据集评测流程 |
| `flow_config_file` | string | 否 | "" | 数据集评测流程配置文件 |
| `use_cache` | bool | 否 | True | 是否使用缓存 |

#### 评测流程配置说明

- `flow_config_file` 如果多个数据集需要复用相同的评测流程，可以将配置写在独立的文件中，通过这个字段复用配置。
- `flow_stages` 评测流程配置，如果没有赋值则使用 `flow_config_file` 文件的内容。

#### 最简配置示例

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
`FlowStage` 是数据集评测流程中一个阶段的完整数据结构。

```python
class FlowStage(BaseModel):
    stage: str = Field(default="")
    plugin_type: PluginType = Field(default=PluginType.NONE_TYPE)
    plugin_implement: str
    context_params: ContextParam = Field(default_factory=dict)
    plugins: list[PluginConfig] = Field(default_factory=list)
    use_cache: bool = Field(default=True)
```

#### 字段说明
| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|------|------|
| `stage` | string | 否 | "" | 阶段名称 |
| `plugin_type` | string | 否 | NONE_TYPE | 阶段插件类型 |
| `plugin_implement` | string | 是 |  | 阶段插件实现类名 |
| `context_params` | dict | 否 | {} | 设置阶段插件参数值 |
| `plugins` | list[PluginConfig] | 否 | [] | 设置步骤插件实现 |
| `use_cache` | bool | 否 | True | 是否使用缓存 |

#### 详细说明 {#flow_stage_detail}

- `stage` 阶段名用于在评测可视化报告中展示，一般可以不填写，默认会设置为当前阶段插件实现类名。
- `plugin_type` 插件类型，一般不需要填写，根据阶段插件实现类自动填充值。
- `plugin_implement` 核心字段，必填，指定当前阶段实现类，决定了是什么样的评测流程。
- `context_params` 可选字段，`plugin_implement` 决定了有哪些参数，可通过这个字段为每个参数赋值，会覆盖插件定义中给定的默认值。 
> **注意** 通过 [plugin_param](#plugin_param) 方式在运行时指定的参数优先级最高，会覆盖这个字段设置的值。
- `plugins` 覆盖步骤插件实现类，可选步骤已经由 `plugin_implement` 定义，未指定覆盖插件的则使用默认实现。以 [SimpleDataProcessor](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/plugin/stage/data/data_processor.py) 数据加载阶段为例，由三个步骤插件组成，各步骤的默认实现类可参考 [PluginLoader](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/plugin_factory.py)。

#### 最简配置示例
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
`PluginConfig` 是数据集评测流程一个阶段的具体一个步骤的完整数据结构。
```python
class PluginConfig(BaseModel):
    plugin_implement: str = Field(default="")
    plugin_type: PluginType = Field(default=PluginType.NONE_TYPE)
    context_params: ContextParam = Field(default_factory=dict)
```
#### 字段说明
| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|------|------|
| `plugin_implement` | string | 是 |  | 步骤插件实现类名 |
| `plugin_type` | string | 否 | NONE_TYPE | 步骤插件类型 |
| `context_params` | dict | 否 | {} | 设置步骤插件参数值 |

#### 详细说明 {#plugin_config_detail}
见阶段插件配置 `FlowStage` 中的 [详细说明](#flow_stage_detail)

#### 最简配置示例
```json
{
    "plugin_implement": "MultiChoiceScenario",
    "context_params":
    {}
}
```

## 配置解析器
解析器主要代码在 [load_benchmark_configs](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/common/param_utils.py) 方法中，主要功能是根据任务配置 [EvalConfig](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/eval_config.py) 生成完整的数据集配置 [BenchmarkConfig](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/flow_config.py)。

### 配置加载
首先需要将数据集配置转换为 [BenchmarkConfig](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/flow_config.py) 对象，目前支持以下几种指定数据集配置的方式：

`agieval start` 命令启动：

- `默认`： 默认加载 [config.py](../common_dataset.md#configpy) 脚本中的变量 `benchmark_config_template`，即 `BenchmarkConfig` 对象。
- `benchmark_config` 参数： 如果指定了该参数则读取文件内容通过 `BenchmarkConfig.model_validate` 方式转换为 `BenchmarkConfig` 对象。

`run.py` 脚本启动：

- `benchmark_config` 参数：同上。

### 模版解析
如果指定了参数 `benchmark_config_template` 则会将上一步加载后的 `BenchmarkConfig` 对象作为数据集配置模版。

- 根据 `dataset_files` 参数解析全部待执行的数据集文件，每个文件作为最小执行单元即数据集。
- 复制配置模版对象，修改数据集名称及文件地址，生成每个数据集的配置文件。

### 参数覆盖
每个插件实现类都要定义自身执行所需的超参数，该参数可以在以下三个层面被赋值：

- `插件默认值`， 参数定义中需要为其设定默认值。如下设定 `base_url` 参数默认值为空字符串：
   
    ```python
    base_url: str = Field(default="", description="Model URL")
    ```

- `数据集配置`， 在数据集配置文件中每个插件实现类可以通过 `context_params` 字段设置其参数值。

    ```json
    {
        "plugin_implement": "LiteLLMModel",
        "context_params":
        {
            "base_url": "http://your-api-endpoint"
        }
    }
    ```

- `运行参数`， 启动评测任务时可通过 `--plugin_param` 字段设置每个参数的运行时值。

    ```bash
    --plugin_param base_url=http://your-api-endpoint
    ```


> **参数优先级**：运行参数 > 数据集配置 > 插件默认值


## 完整配置示例
<details>
<summary>示例</summary>

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

