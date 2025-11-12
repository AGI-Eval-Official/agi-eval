# 公开数据集

## 概述
框架已适配了部分公开数据集可直接使用，本节将介绍如何将一个已适配完成的新数据集配置成一个公开数据集。

配置公开数据集需要完成以下步骤：

1. 适配数据集。
2. 配置数据集评测流程。
3. 上传数据集文件（可选）。

## 适配数据集

适配过程请查看 [适配数据集](./custom_dataset.md)

### 组织文件格式
一个公开数据集要满足如下目录结构：
```bash
dataset_name /               # 数据集名字
├── _dataset_location.txt /  # 数据集文件索引
├── dataset_1.json /         # 数据集文件
├── dataset_2.json /         # 数据集文件
├── ...
└── dataset_n.json /         # 数据集文件
```
- `dataset_name` 数据集名字作为文件夹名字。

- `_dataset_location.txt` 文本文件描述数据集文件集合，共两列, 第一列为数据集文件名, 第二列为数据集名称（非必填，默认取文件名）。示例如下：
    - **特别注意**：在框架执行时会将每个数据文件认为是一个独立的数据集，多个数据文件可并行评测。
```bash
dataset_1.json, dataset_1
dataset_2.json, dataset_2
dataset_n.json, dataset_n
```
- `dataset_1.json`  数据集文件，内容为具体的评测数据。

### 数据集目录
公开数据集的数据需要放在项目根目录的 `datasets` 文件夹下，完整的目录结构如下:
```bash
llm-eval-opensource /
└── datasets /
    └── dataset_name /
        ├── _dataset_location.txt /
        ├── dataset_1.json /
        ├── dataset_2.json /
        ├── ... /
        └── dataset_n.json /
```


## 配置评测流程
公开数据集的评测流程配置文件需要放在项目根目录的 `example` 目录下。

### config.py
`config.py` 脚本是最重要的配置文件，框架会读取该文件解析评测任务配置与评测流程配置。

文件目录结构要求如下：
```bash
example /
    └── dataset /
        └── dataset_name  # 数据集名字 
            └── config.py
```
> **注意**：数据集名字要求必须与前述 [组织文件格式](#组织文件格式) 中 `dataset_name` 一致。

在该文件中需要初始化两个变量：

- `eval_config` 评测任务配置对象，类型为 [EvalConfig](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/eval_config.py)。
- `benchmark_config_template` 评测数据集配置模板对象，类型为 [BenchmarkConfig](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/flow_config.py)

> 两个对象数据结构的详细介绍查看 [配置管理](./component/config_manager.md)。

示例如下:
```python
eval_config: EvalConfig = EvalConfig(
    runner=RunnerType.DATA_PARALLEL,
    benchmark_config_template=True,   # 开启评测数据集配置模板模式
    dataset_files=f"datasets/{dataset_name}",  # 数据集文件下载/存储目录
    benchmark_config="",
    flow_config_file="",
    work_dir=f"result/{dataset_name}",
    data_parallel=2,
    global_param=GlobalParam(),
    plugin_param=ContextParam(
        **load_model_api_config()  # 读取模型API配置并设置到运行时参数
    )
)

# 评测数据集配置模板
benchmark_config_template = BenchmarkConfig(
    benchmark="",  # 置空，框架会自动赋值
    location_test="", # 置空，框架会自动赋值
    use_cache=False,
    flow_config_file=f"example/flow_config/{dataset_name}.json",
    flow_stages=[   # 与 flow_config_file 二选一
    ]
)
```

### flow_config.json
如果在评测流程是可复用的，则可以创建独立的文件存储，其他数据集可直接引用该文件，无需重复配置。

该文件存储位置可自定义，没有强制要求，但建议放在 `example/flow_config` 目录下。

文件内容如何编写请查看 [配置管理](./component/config_manager.md)。



## 上传数据集文件（可选）
### 贡献社区
框架已适配的公开数据集的数据文件存放在 [数据集仓库](https://github.com/AGI-Eval-Official/agi-eval-benchmarks) 中，如果想将数据集共享给社区用户需要将数据文件上传至该仓库。

数据集目录需要放置在仓库的根目录下。

### 内部共享
如果只需要小范围内共享使用，可以将数据集目录上传至任意共享存储上，然后修改数据集下载功能支持从对应存储下载数据文件即可。

数据集下载功能适配方式如下：

1. 在 [download_util.py](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/common/dataset_util.py) 文件中增加数据集下载方法，需要接受如下两个参数：

    - `dataset` 要下载的数据集名字。
    - `dataset_dir` 数据集下载后的存储路径。
    
2. 在评测入口 [main.py](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/cli/main.py) 文件中的 `run_example_dataset` 方法中判断下载方式，参考如下：
```python
def run_example_dataset(dataset, eval_config: EvalConfig, benchmark_config_template: BenchmarkConfig):
    with ProcessContext(eval_config):
        setup_logger(eval_config.work_dir, eval_config.debug)
        if eval_config.benchmark_config:
            eval_config.benchmark_config_template = False
            benchmark_configs = load_benchmark_configs(eval_config, eval_config.benchmark_config, "")
        else:
            eval_config.dataset_files = os.path.join(os.getcwd(), eval_config.dataset_files)
            if not download_dataset_from_git(dataset, eval_config.dataset_files):
                log_error("Dataset download failed, terminating subsequent evaluation process")
                raise Exception("Dataset download failed")
            benchmark_configs = load_benchmark_configs(eval_config, benchmark_config_template, "")
        
        run_with_eval_config(eval_config, benchmark_configs)
```