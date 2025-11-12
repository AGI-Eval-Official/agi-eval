# Start Evaluation

## Overview
This section will detail how to start an evaluation task.

The framework supports two startup methods: Command Line Interface (CLI) and Python script.

## Environment Setup
Before starting the task, please ensure that the framework and all dependencies are installed. For details, refer to [Environment Setup](./installation.md).

## Command Line Interface (CLI)
The framework supports starting evaluation tasks through the `agieval start` command. For more commands, refer to [Command Line Tool](./agieval_cli.md).

For public datasets already adapted and supported by the framework or datasets adapted according to framework requirements, it is recommended to use the Command Line Interface (CLI) for evaluation.

### Example
Simple startup command:
```bash
agieval start test
```
Complete startup command
```bash
agieval start test \
    --runner dummy \
    --benchmark_config example/dataset/test/benchmark_config.json \
    --global_param k1=v1 k2=v2 \
    --plugin_param base_url=http://your-api-endpoint model=your-model-name api_key=your-api-key
```
### Parameter Description {#cli_param}
| Field Name | Type | Required | Default | Description |
|------------|------|----------|---------|-------------|
|      | string | Yes |  | Name of the dataset to evaluate |
| `debug` | bool | No | False | Enable debug mode |
| `runner` | string | No | dummy | Evaluation executor type |
| `benchmark_config` | string | No |  | Dataset configuration file |
| `global_param` | string | No | "" | Global parameters, overriding default parameters in dataset configuration |
| `plugin_param` | string | No | "" | Plugin parameters, overriding default parameters in dataset configuration |

#### Detailed Description
Required parameters

- Name of the dataset to evaluate, the first positional parameter required by the `agieval start` command, optional values can be viewed through the `agieval benchmarks` command. The framework will parse complete evaluation parameters based on the [config.py](./common_dataset.md#configpy) script bound to this dataset.

Optional parameters

> Optional parameters will override parameters in the [config.py](./common_dataset.md#configpy) script bound to the dataset, equivalent to temporarily modifying this script. For detailed description of each parameter, refer to [Detailed Parameter Description](./component/config_manager.md#eval_config_detail).

- `--debug` Enable debug mode
- `--runner` Evaluation executor type
- `--benchmark_config` Dataset configuration file
    - **Special note**: This parameter will simultaneously force modify the `benchmark_config_template` parameter in the `config.py` script to False.
- `--global_param` Global parameters, overriding default parameters in dataset configuration
- `--plugin_param` Plugin parameters, overriding default parameters in dataset configuration


## Python Script
The Python script execution entry is [run.py](https://github.com/AGI-Eval-Official/agi-eval/blob/master/run.py).

For new datasets that require secondary development of the framework for adaptation, it is recommended to use Python scripts for evaluation.

### Example
```bash
python3 run.py \
    --debug \
    --runner data_parallel \
    --benchmark_config_template  \
    --dataset_files datasets/test \
    --benchmark_config example/dataset/test/benchmark_config.json \
    --flow_config_file example/flow_config/default_flow.json \
    --work_dir result/test \
    --data_parallel 2 \
    --global_param k1=v1 k2=v2 \
    --plugin_param base_url=http://your-api-endpoint model=your-model-name api_key=your-api-key
```

### Parameter Description {#python_param}
For detailed parameter description, refer to [Detailed Parameter Description](./component/config_manager.md#eval_config_detail)

## Summary
The difference between using the Command Line Interface (CLI) or Python script to start evaluation is just the different parameter passing methods. Through the [Configuration Parser](./component/config_manager.md#configuration-parser), they will be uniformly converted to complete dataset configurations. For complete dataset configuration examples, refer to [Complete Configuration Example](./component/config_manager.md#complete-configuration-example).

> Command Line Interface (CLI) is suitable for datasets with mature evaluation processes, i.e., evaluating adapted [Public Datasets](./common_dataset.md).

> Python scripts are suitable for secondary development of the framework, i.e., testing various custom plugins developed for new datasets according to the [Plugin Development Guide](./component/plugin_guides.md).
