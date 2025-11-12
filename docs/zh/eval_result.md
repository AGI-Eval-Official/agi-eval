# 评测结果

## 概述
本节将介绍评测结果的数据结构以及可视化服务。

## 数据结构
评测结果存储地址由 [work_dir](./component/config_manager.md#work_dir) 决定。

### 目录结构
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
### 详细说明

#### logs
评测日志文件，存储评测过程中产生的日志信息。

#### benchmark_config.json
通过 [配置解析器](./component/config_manager.md#配置解析器) 统一转换的完整数据集配置文件，详细信息查看 [数据集配置](./component/config_manager.md#数据集配置)

#### eval_config.json
评测任务配置，详细信息查看 [任务配置](./component/config_manager.md#任务配置)。

#### dataset
各数据集的评测结果以及中间数据。

- `scenario_state.json` 存储数据集的每一条数据以及其模型推理结果。
- `per_instance_stats.json` 存储数据集的每一条数据的评测结果，即各项评测指标。
- `stats.json` 存储数据集的最终评测结果，即各项评测指标的平均值。

## 可视化
框架内置了评测结果可视化服务，支持对评测结果进行简单的可视化展示。

### 启动方式
#### 单独启动
可通过 `agieval appstart` 命令启动可视化服务，详见 [启动评测结果可视化服务](./agieval_cli.md#启动评测结果可视化服务)

#### 自动启动
评测流程中 `报告生成阶段` 可用于生成评测报告，目前框架内置实现了 `可视化报告生成器` 即 `report` 类型的步骤插件。

在评测流程中配置报告生成阶段，即可自动启动可视化服务。
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

### 报告介绍

<table>
  <tr>
    <td style="text-align: center;">
      <img src="images/metrics.png" alt="评测指标" style="width: 100%;" />
      <p>评测指标</p>
    </td>
    <td style="text-align: center;">
      <img src="images/detail.png" alt="评测详情" style="width: 100%;" />
      <p>评测详情</p>
    </td>
  </tr>
  <tr>
    <td style="text-align: center;">
      <img src="images/param.png" alt="评测参数" style="width: 100%;" />
      <p>评测参数</p>
    </td>
    <td style="text-align: center;">
      <img src="images/flow.png" alt="评测流程" style="width: 100%;" />
      <p>评测流程</p>
    </td>
  </tr>
</table>



