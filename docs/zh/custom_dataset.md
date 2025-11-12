# 适配数据集

## 概述
框架已内置适配了部分公开数据集可直接使用，本节将介绍如何适配一个新的数据集。

适配一个数据集之前需要先理解框架的 [插件体系](./component/plugin_system.md#插件实现) ，并且了解各插件具体实现的功能。在此基础上可以分两种情况：

- `适配数据结构` 当前插件实现已满足评测流程需要，只需将数据集的数据结构转换为框架要求的标准结构。
- `适配评测流程` 当前插件不足以完成评测任务，需要实现新的插件才能满足需要。

以上两者并不冲突，`适配数据结构` 后可能还需要`适配评测流程`中的指标计算插件满足自定义的指标计算需求。

## 适配数据结构
需要离线将数据集内容转换为标准格式，有`生成题`和`选择题`两种格式可选。

### 生成题
#### 标准格式
每一条数据包含`input`和`target`两个字段。
<details>
<summary>示例</summary>

```json
{
    "examples":
    [
        {
            "input": "Find the sum of all integer bases $b>9$ for which $17_b$ is a divisor of $97_b.$",
            "target": "70"
        }
    ]
}
```
</details>

#### 数据加载阶段配置
<details>
<summary>示例</summary>

```json
{
    "plugin_implement": "SimpleDataProcessor",
    "plugins":
    [
        {
            "plugin_implement": "GenerationScenario"
        },
        {
            "plugin_implement": "GenerationAdapter"
        }
    ]
}
```
</details>

### 选择题
每一条数据包含`input`和`target_scores`两个字段，`target_scores`中要求正确答案对应value置为1，其余置为0。

<details>
<summary>示例</summary>

```json
{
    "examples":
    [
        {
          "input": "以下是关于解剖学的单项选择题，请直接给出正确答案的选项。\n\n题目：直接和语言活动有关的中枢\nA. 额中回后分\nB. 角回\nC. 顶上小叶缘上回\nD. 额下回后分\n",
          "target_scores": {
            "额中回后分": 0,
            "顶上小叶缘上回": 0,
            "额下回后分": 1,
            "角回": 0
          }
        }
    ]
}
```
</details>

#### 数据加载阶段配置
<details>
<summary>示例</summary>

```json
{
    "plugin_implement": "SimpleDataProcessor",
    "plugins":
    [
        {
            "plugin_implement": "MultipleChoiceScenario"
        },
        {
            "plugin_implement": "BaseMultiChoiceAdapter"
        }
    ]
}
```
</details>

## 适配评测流程
评测流程的适配一般集中在数据加载阶段、指标计算阶段两部分。具体开发方式查看 [插件开发指南](./component/plugin_guides.md#增加步骤插件)。

### 数据加载阶段
如果已离线完成了 [数据结构适配](#适配数据结构) 过程，则无需这一步。实际上，离线完成的数据结构适配过程也就等同于完成了数据加载阶段的适配。

这一步主要是开发一个 `scenario` 类型的插件，需要完成的功能如下：

1. 根据benchmark_path参数对应数据集地址读取数据文件内容。
2. 解析每一条数据，拼接完整的模型输入prompt。
3. 构造 `Instance` 结构返回。


### 指标计算阶段
框架内置了一些指标计算规则，请先查看内置的各 [指标计算插件](https://github.com/AGI-Eval-Official/agi-eval/tree/master/agieval/plugin/metrics) 判断是否满足需求。

这一步主要是开发一个 `metrics` 类型的插件，从 `ScenarioState` 类型的输入中获取模型推理结果、标准答案等信息，实现自定义的指标计算规则，最后封装`Stat`对象返回。


## 编写配置文件
框架要求每个数据集必须绑定一个配置文件，用于描述数据集的基本信息以及评测流程。配置文件介绍请查看 [数据集配置](./component/config_manager.md#数据集配置)

最简单的数据集配置必填字段说明：

- `benchmark` 数据集名字
- `location_test` 数据集文件地址
- `flow_stages` 评测流程

其中评测流程里各阶段下的步骤插件可替换为自定义插件实现。

<details>
<summary>完整示例如下</summary>

```json
[
    {
        "benchmark": "test",
        "location_test": "dataset/test/test.json",
        "flow_stages":
        [
            {
                "plugin_implement": "SimpleDataProcessor",
                "plugins":
                [
                    {
                        "plugin_implement": "GenerationScenario"
                    }
                ]
            },
            {
                "plugin_implement": "SimpleInferProcessor",
                "plugins":
                [
                    {
                        "plugin_implement": "LiteLLMModel"
                    },
                    {
                        "plugin_implement": "SingleRoundTextAgent"
                    }
                ]
            },
            {
                "plugin_implement": "SimpleMetricsProcessor",
                "plugins":
                [
                    {
                        "plugin_implement": "QuasiPrefixExactMatchMetrics"
                    }
                ]
            },
            {
                "plugin_implement": "SimpleReportProcessor",
                "plugins":
                [
                    {
                        "plugin_implement": "VisualizationReport"
                    }
                ]
            }
        ]
    }
]
```
</details>