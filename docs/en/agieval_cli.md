# Command Line Tool

## Overview
This section introduces how to use the framework capabilities through the command line tool.

## Tool Introduction
The `agi-eval` command line tool (CLI) only supports installation through `pip install -e .` for local debugging, and does not provide online installation methods.

For details, refer to [Environment Setup](./installation.md).

## Detailed Command Introduction
You can view usage help through the `agieval -help` command.

### Tool Version
```bash
agieval -v

# Output example
# AGI-Eval 1.0.0
```

### View List of Adapted Datasets
```bash
agieval benchmarks
```
Output example
```bash
Adapted benchmarks:
AIME2024, AIME2025, BBEH, BBH-Cot-3Shot, BeyondAIME, CEval, CMMLU, DROP, GPQA, GSM8K, IFEval, MATH, MATH-500, MGSM, MMLU, MMLU-Pro, MMLU-Redux, MMMLU, OlympiadBench, SimpleQA, SuperGPQA, mIFEval, test
```

### Start Evaluation Task
```bash
agieval start test
```
Required parameters

  - Dataset name, optional values are adapted dataset names.

Optional parameters

  - --debug, enable debug mode, override the debug field in dataset configuration.
  - --runner, running method, override the runner field in dataset configuration.
  - --benchmark_config, dataset configuration file, override the benchmark_config field in dataset configuration.

For detailed instructions, refer to [Parameter Description](./start_task.md#cli_param)

Output example
```bash
# If the task starts successfully, it will output process id and log file address
Task process started successfully pid: 8059, log path: /home/user/result/test/logs/info.log
```


### View Running Evaluation Tasks
```bash
agieval status
```
Output example
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

### Stop Evaluation Task
Stop all tasks
```bash
agieval stop
```
Stop specified tasks
```bash
agieval stop 8059 8060
```
Output example
```bash
Starting to stop evaluation tasks: 8059 8060
Evaluation task stopped: 8059
Evaluation task stopped: 8060
All evaluation tasks have been stopped
```



### Start Evaluation Result Visualization Service
```bash
agieval appstart --result_dir=result/test
```
Required parameters

  - --result_dir=result/test, specify the directory where evaluation results are located

Optional parameters

  - --port=38410, evaluation service listening port, default is `38410`

Output example
```bash
Visit the following URL to view the evaluation report: http://localhost:38410/agieval/visualization/reportor.html?path=result/test
```
For detailed introduction, refer to [Evaluation Results](./eval_result.md#visualization).
### Stop Evaluation Result Visualization Service
```bash
agieval appstop
```
Output example
```bash
Evaluation result visualization service stopped: 53923
