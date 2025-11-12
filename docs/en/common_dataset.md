# Public Datasets

## Overview
The framework has adapted some public datasets that can be used directly. This section introduces how to configure a newly adapted dataset as a public dataset.

Configuring a public dataset requires the following steps:

1. Adapt the dataset.
2. Configure dataset evaluation process.
3. Upload dataset files (optional).

## Adapt Dataset

For the adaptation process, please refer to [Adapting Datasets](./custom_dataset.md)

### Organize File Format
A public dataset should meet the following directory structure:
```bash
dataset_name /               # Dataset name
├── _dataset_location.txt /  # Dataset file index
├── dataset_1.json /         # Dataset file
├── dataset_2.json /         # Dataset file
├── ...
└── dataset_n.json /         # Dataset file
```
- `dataset_name` The dataset name is used as the folder name.

- `_dataset_location.txt` A text file describing the collection of dataset files, with two columns: the first column is the dataset file name, the second column is the dataset name (optional, defaults to file name). Example as follows:
    - **Special note**: During framework execution, each data file will be considered an independent dataset, and multiple data files can be evaluated in parallel.
```bash
dataset_1.json, dataset_1
dataset_2.json, dataset_2
dataset_n.json, dataset_n
```
- `dataset_1.json` Dataset file, containing specific evaluation data.

### Dataset Directory
Public dataset data needs to be placed in the `datasets` folder in the project root directory. The complete directory structure is as follows:
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

## Configure Evaluation Process
The evaluation process configuration file for public datasets needs to be placed in the `example` directory in the project root.

### config.py
The `config.py` script is the most important configuration file. The framework will read this file to parse evaluation task configuration and evaluation process configuration.

The file directory structure requirements are as follows:
```bash
example /
    └── dataset /
        └── dataset_name  # Dataset name
            └── config.py
```
> **Note**: The dataset name must be consistent with the `dataset_name` in the aforementioned [Organize File Format](#organize-file-format).

In this file, you need to initialize two variables:

- `eval_config` Evaluation task configuration object, type is [EvalConfig](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/eval_config.py).
- `benchmark_config_template` Evaluation dataset configuration template object, type is [BenchmarkConfig](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/flow_config.py)

> For detailed introduction to the data structures of these two objects, refer to [Configuration Management](./component/config_manager.md).

Example as follows:
```python
eval_config: EvalConfig = EvalConfig(
    runner=RunnerType.DATA_PARALLEL,
    benchmark_config_template=True,   # Enable evaluation dataset configuration template mode
    dataset_files=f"datasets/{dataset_name}",  # Dataset file download/storage directory
    benchmark_config="",
    flow_config_file="",
    work_dir=f"result/{dataset_name}",
    data_parallel=2,
    global_param=GlobalParam(),
    plugin_param=ContextParam(
        **load_model_api_config()  # Read model API configuration and set to runtime parameters
    )
)

# Evaluation dataset configuration template
benchmark_config_template = BenchmarkConfig(
    benchmark="",  # Leave empty, framework will automatically assign
    location_test="", # Leave empty, framework will automatically assign
    use_cache=False,
    flow_config_file=f"example/flow_config/{dataset_name}.json",
    flow_stages=[   # Alternative to flow_config_file
    ]
)
```

### flow_config.json
If the evaluation process is reusable, you can create an independent file for storage, and other datasets can directly reference this file without repeated configuration.

The storage location of this file can be customized and is not mandatory, but it is recommended to place it in the `example/flow_config` directory.

For how to write the file content, please refer to [Configuration Management](./component/config_manager.md).


## Upload Dataset Files (optional)
### Contribute to Community
The data files of public datasets adapted by the framework are stored in the [Dataset Repository](https://github.com/AGI-Eval-Official/agi-eval-benchmarks). If you want to share the dataset with community users, you need to upload the data files to this repository.

The dataset directory needs to be placed in the root directory of the repository.

### Internal Sharing
If you only need to share within a small scope, you can upload the dataset directory to any shared storage, and then modify the dataset download functionality to support downloading data files from the corresponding storage.

The dataset download functionality adaptation is as follows:

1. Add a dataset download method in the [download_util.py](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/common/dataset_util.py) file, which needs to accept the following two parameters:

    - `dataset` The name of the dataset to download.
    - `dataset_dir` The storage path after dataset download.

2. In the evaluation entry [main.py](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/cli/main.py) file, determine the download method in the `run_example_dataset` method, reference as follows:
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