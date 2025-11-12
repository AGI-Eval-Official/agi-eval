# Evaluation Results

## Overview
This section introduces the data structure of evaluation results and visualization services.

## Data Structure
The storage address of evaluation results is determined by [work_dir](./component/config_manager.md#work_dir).

### Directory Structure
```bash
work_dir
├── dataset_1
├── dataset_2
├── dataset_3
│   ├── per_instance_stats.json
│   ├── scenario_state.json
│   ├── stats.json
├── logs
├── benchmark_config.json
└── eval_config.json
```
### Detailed Description

#### logs
Evaluation log files, storing log information generated during the evaluation process.

#### benchmark_config.json
The complete dataset configuration file uniformly converted through the [Configuration Parser](./component/config_manager.md#configuration-parser). For detailed information, refer to [Dataset Configuration](./component/config_manager.md#dataset-configuration)

#### eval_config.json
Evaluation task configuration. For detailed information, refer to [Task Configuration](./component/config_manager.md#task-configuration).

#### dataset
Evaluation results and intermediate data for each dataset.

- `scenario_state.json` Stores each piece of data in the dataset and its model inference results.
- `per_instance_stats.json` Stores the evaluation results of each piece of data in the dataset, i.e., various evaluation metrics.
- `stats.json` Stores the final evaluation results of the dataset, i.e., the average values of various evaluation metrics.

## Visualization
The framework has built-in evaluation result visualization services that support simple visualization display of evaluation results.

### Startup Methods
#### Standalone Startup
You can start the visualization service through the `agieval appstart` command. For details, refer to [Start Evaluation Result Visualization Service](./agieval_cli.md#start-evaluation-result-visualization-service)

#### Auto Startup
The `Report Generation Stage` in the evaluation process can be used to generate evaluation reports. Currently, the framework has built-in implementation of the `Visualization Report Generator`, which is a `report` type step plugin.

Configure the report generation stage in the evaluation process to automatically start the visualization service.
```json
{
    "plugin_implement": "SimpleReportProcessor",
    "plugins":
    [
        {
            "plugin_implement": "VisualizationReport"
        }
    ]
}
```

### Report Introduction

<table>
  <tr>
    <td style="text-align: center;">
      <img src="images/metrics.png" alt="Evaluation Metrics" style="width: 100%;" />
      <p>Evaluation Metrics</p>
    </td>
    <td style="text-align: center;">
      <img src="images/detail.png" alt="Evaluation Details" style="width: 100%;" />
      <p>Evaluation Details</p>
    </td>
  </tr>
  <tr>
    <td style="text-align: center;">
      <img src="images/param.png" alt="Evaluation Parameters" style="width: 100%;" />
      <p>Evaluation Parameters</p>
    </td>
    <td style="text-align: center;">
      <img src="images/flow.png" alt="Evaluation Process" style="width: 100%;" />
      <p>Evaluation Process</p>
    </td>
  </tr>
</table>
