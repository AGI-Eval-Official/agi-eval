# 开始评测

## 概述
本节将详细介绍如何启动一个评测任务。

框架支持两种启动方式： 命令行界面 (CLI) 和 Python 脚本。

## 环境准备
在启动任务之前，请确保已经安装了框架和所有依赖库，详情查看 [环境准备](./installation.md)。

## 命令行界面 (CLI)
框架支持通过 `agieval start` 命令启动评测任务，更多命令查看 [命令行工具](./agieval_cli.md)。

对于框架已适配支持的公开数据集或者按框架要求自行适配好的数据集，推荐使用命令行界面 (CLI) 进行评测。

### 示例
最简启动命令：
```bash
agieval start test
```
完整启动命令
```bash
agieval start test \
    --runner dummy \
    --benchmark_config example/dataset/test/benchmark_config.json \
    --global_param k1=v1 k2=v2 \
    --plugin_param base_url=http://your-api-endpoint model=your-model-name api_key=your-api-key
```
### 参数说明 {#cli_param}
| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|------|------|
|      | string | 是 |  | 评测的数据集名称 |
| `debug` | bool | 否 | False | 开启debug模式 |
| `runner` | string | 否 | dummy | 评测执行器类型 |
| `benchmark_config` | string | 否 |  | 数据集配置文件 |
| `global_param` | string | 否 | "" | 全局参数，覆盖数据集配置中的默认参数 |
| `plugin_param` | string | 否 | "" | 插件参数，覆盖数据集配置中的默认参数 |

#### 详细说明
必填参数

-  评测的数据集名称，`agieval start` 命令要求的第一个位置参数，可选值通过 `agieval benchmarks` 命令查看。框架会根据该数据集绑定的 [config.py](./common_dataset.md#configpy) 脚本解析完整的评测参数。

选填参数

> 选填参数将覆盖数据集绑定的 [config.py](./common_dataset.md#configpy) 脚本中的参数，相当于临时修改该脚本，查看各参数 [详细说明](./component/config_manager.md#eval_config_detail)。

- `--debug` 开启debug模式
- `--runner` 评测执行器类型
- `--benchmark_config` 数据集配置文件
    - **特别注意**：该参数将同步强制修改 `config.py` 脚本中的 `benchmark_config_template` 参数为 False。
- `--global_param` 全局参数，覆盖数据集配置中的默认参数
- `--plugin_param` 插件参数，覆盖数据集配置中的默认参数


## Python 脚本
python脚本执行入口是 [run.py](https://github.com/AGI-Eval-Official/agi-eval/blob/master/run.py)。

对于适配需要对框架进行二次开发的新数据集，推荐使用 Python 脚本进行评测。

### 示例
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

### 参数说明 {#python_param}
查看参数 [详细说明](./component/config_manager.md#eval_config_detail)

## 总结
使用命令行界面 (CLI) 或者 Python 脚本开始评测的区别只是参数传递方式不同，通过 [配置解析器](./component/config_manager.md#配置解析器) 将统一转换为完整的数据集配置，[数据集配置完整示例](./component/config_manager.md#完整配置示例)。 

> 命令行界面 (CLI) 适合有成熟的评测流程的数据集，即评测已适配的 [公开数据集](./common_dataset.md)。

> Python 脚本适合对框架进行二次开发，即测试根据 [插件开发指南](./component/plugin_guides.md) 开发的新数据集的各类自定义插件。

