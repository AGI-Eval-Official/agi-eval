# 命令行工具

## 概述
本节将介绍如何通过命令行工具使用框架能力。

## 工具介绍
`agi-eval` 命令行工具 (CLI) 只支持通过 `pip install -e . ` 本地调试的方式安装，未提供在线安装方式。

详情查看 [环境准备](./installation.md) 。

## 详细命令介绍
可通过 `agieval -help` 命令查看使用帮助。

### 工具版本
```bash
agieval -v

# 输出示例
# AGI-Eval 1.0.0
```

### 查看已适配的数据集列表
```bash
agieval benchmarks
```
输出示例
```bash
Adapted benchmarks:
AIME2024, AIME2025, BBEH, BBH-Cot-3Shot, BeyondAIME, CEval, CMMLU, DROP, GPQA, GSM8K, IFEval, MATH, MATH-500, MGSM, MMLU, MMLU-Pro, MMLU-Redux, MMMLU, OlympiadBench, SimpleQA, SuperGPQA, mIFEval, test
```

### 启动评测任务
```bash
agieval start test
```
必填参数

  - 数据集名称，可选值是已适配的数据集名称。

可选参数

  - --debug，开启debug模式，覆盖数据集配置中的 debug 字段。
  - --runner，运行方式，覆盖数据集配置中的 runner 字段。
  - --benchmark_config，数据集配置文件，覆盖数据集配置中的 benchmark_config 字段。

详细说明查看 [参数说明](./start_task.md#cli_param)

输出示例
```bash
# 任务启动成功则会输出进程id及日志文件地址
Task process started successfully pid: 8059, log path: /home/user/result/test/logs/info.log
```


### 查看运行中的评测任务
```bash
agieval status
```
输出示例
```bash
AGI-Eval running task pids: 8059
AGI-Eval running task configs:
{
    "8059":
    {
        "debug": false,
        "runner": "data_parallel",
        "benchmark_config_template": true,
        "dataset_files": "datasets/test",
        "benchmark_config": "",
        "flow_config_file": "",
        "work_dir": "result/test",
        "data_parallel": 10,
        "global_param":
        {},
        "plugin_param":
        {
            "base_url": "http://your-api-endpoint",
            "model": "your-model-name",
            "api_key": "your-api-key"
        }
    }
}
```

### 中止评测任务
中止全部任务
```bash
agieval stop
```
中止指定任务
```bash
agieval stop 8059 8060
```
输出示例
```bash
Starting to stop evaluation tasks: 8059 8060
Evaluation task stopped: 8059
Evaluation task stopped: 8060
All evaluation tasks have been stopped
```



### 启动评测结果可视化服务
```bash
agieval appstart --result_dir=result/test
```
必填参数

  - --result_dir=result/test，指定评测结果所在目录

选填参数

  - --port=38410，评测服务监听端口，默认为`38410`

输出示例
```bash
Visit the following URL to view the evaluation report: http://localhost:38410/agieval/visualization/reportor.html?path=result/test
```
详细介绍查看 [评测结果](./eval_result.md#可视化)。
### 停止评测结果可视化服务
```bash
agieval appstop
```
输出示例
```bash
Evaluation result visualization service stopped: 53923
```

