# Adapting Datasets

## Overview
The framework has built-in adaptations for some public datasets that can be used directly. This section introduces how to adapt a new dataset.

Before adapting a dataset, you need to first understand the framework's [Plugin System](./component/plugin_system.md#plugin-implementation) and know the specific functions implemented by each plugin. Based on this, there are two scenarios:

- `Adapt Data Structure` The current plugin implementations already meet the evaluation process needs, only need to convert the dataset's data structure to the standard structure required by the framework.
- `Adapt Evaluation Process` The current plugins are not sufficient to complete the evaluation task, and new plugins need to be implemented to meet the requirements.

These two are not mutually exclusive. After `Adapt Data Structure`, you may still need to adapt the metric calculation plugins in `Adapt Evaluation Process` to meet custom metric calculation needs.

## Adapt Data Structure
You need to offline convert the dataset content to the standard format, with two optional formats: `Generation Questions` and `Multiple Choice Questions`.

### Generation Questions
#### Standard Format
Each piece of data contains two fields: `input` and `target`.
<details>
<summary>Example</summary>

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

#### Data Loading Stage Configuration
<details>
<summary>Example</summary>

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

### Multiple Choice Questions
Each piece of data contains two fields: `input` and `target_scores`. In `target_scores`, the correct answer's corresponding value should be set to 1, and the rest should be set to 0.

<details>
<summary>Example</summary>

```json
{
    "examples":
    [
        {
          "input": "The following is a single-choice question about anatomy. Please directly give the correct answer option.\n\nQuestion: The center directly related to language activities\nA. Posterior part of middle frontal gyrus\nB. Angular gyrus\nC. Supramarginal gyrus of superior parietal lobule\nD. Posterior part of inferior frontal gyrus\n",
          "target_scores": {
            "Posterior part of middle frontal gyrus": 0,
            "Supramarginal gyrus of superior parietal lobule": 0,
            "Posterior part of inferior frontal gyrus": 1,
            "Angular gyrus": 0
          }
        }
    ]
}
```
</details>

#### Data Loading Stage Configuration
<details>
<summary>Example</summary>

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

## Adapt Evaluation Process
The adaptation of the evaluation process is generally concentrated in two parts: the data loading stage and the metric calculation stage. For specific development methods, refer to [Plugin Development Guide](./component/plugin_guides.md#add-step-plugin).

### Data Loading Stage
If you have already completed the [Data Structure Adaptation](#adapt-data-structure) process offline, this step is not needed. In fact, the data structure adaptation process completed offline is equivalent to completing the adaptation of the data loading stage.

This step mainly involves developing a `scenario` type plugin that needs to complete the following functions:

1. Read data file content according to the dataset address corresponding to the benchmark_path parameter.
2. Parse each piece of data and construct the complete model input prompt.
3. Construct and return an `Instance` structure.


### Metric Calculation Stage
The framework has built-in some metric calculation rules. Please first check the built-in [Metric Calculation Plugins](https://github.com/AGI-Eval-Official/agi-eval/tree/master/agieval/plugin/metrics) to determine if they meet your needs.

This step mainly involves developing a `metrics` type plugin that obtains model inference results, standard answers, and other information from `ScenarioState` type input, implements custom metric calculation rules, and finally encapsulates and returns a `Stat` object.


## Write Configuration File
The framework requires each dataset to be bound to a configuration file to describe the basic information of the dataset and the evaluation process. For configuration file introduction, please refer to [Dataset Configuration](./component/config_manager.md#dataset-configuration)

Required field descriptions for the simplest dataset configuration:

- `benchmark` Dataset name
- `location_test` Dataset file address
- `flow_stages` Evaluation process

The step plugins under each stage in the evaluation process can be replaced with custom plugin implementations.

<details>
<summary>Complete example as follows</summary>

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
