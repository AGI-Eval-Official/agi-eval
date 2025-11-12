# 插件系统

## 概述

插件系统位于 [agieval/core/plugin](https://github.com/AGI-Eval-Official/agi-eval/tree/master/agieval/plugin) ，负责插件的定义、注册、加载和执行。它采用泛型设计，提供了类型安全的插件接口。 

## 目录结构

```bash
agieval/
└── core/
    └── plugin/          
        ├── base_plugin.py          # 插件基类
        ├── base_plugin_param.py    # 插件参数基类
        ├── plugin_factory.py       # 插件工厂类
        └── plugins_decorator.py    # 插件装饰器
```

## 插件定义

### PluginType
[PluginType](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/flow_config.py) 定义了全部的插件类型，同类型的不同插件通过各自的策略能够达成同一个目的，即策略模式的具体实现。

每个插件都需要通过插件装饰器确定其插件类型，插件工厂则根据插件类型识别并加载插件。


### BasePlugin
[BasePlugin](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin.py) 是所有插件的基类，定义了插件的基本接口和行为。

主要特性：

- 泛型支持：通过泛型参数管理插件自定义参数。
- 自动配置验证：使用 Pydantic 进行配置验证。
- 日志支持：内置日志记录功能。

插件分为`阶段插件`与`步骤插件`两大类。

### BaseStage
[BaseStage](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin.py) 是阶段插件的基类，继承自 [BasePlugin](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin.py) ，用于管理评测流程的主要阶段，核心功能是调度多个子步骤执行。阶段的定义是可独立运行的功能模块，阶段间的任意组合代表了一种评测流程的具体实现。

主要特性：

- 缓存支持：支持结果缓存，避免重复计算，提供缓存可用性检查接口。
- 步骤管理：定义阶段包含的处理步骤，每一步对应一个步骤插件。

其中每个步骤都应该只定义插件类型，具体实现由运行时配置的步骤插件实现类决定。

### BaseStep
[BaseStep](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin.py) 是步骤插件的基类，继承自 [BasePlugin](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin.py) ，用于实现具体的处理步骤。

步骤插件不能单独使用，必须作为阶段插件的子组件存在。


## 插件参数

每个插件都必须指定对应的参数类，定义插件执行时可调节的超参数。

### BasePluginParam
[BasePluginParam](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin_param.py) 继承自Pydantic的 **BaseModel** ，是所有插件参数的基类，定义了所有插件共有的参数以及通用的参数值处理方法。

- `benchmark_id` 执行的数据集名字。
- `work_dir` 本次评测的输出目录。

### BaseStagePluginParam
[BaseStagePluginParam](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin_param.py) 继承自 [BasePluginParam](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin_param.py)，是阶段插件的参数基类。

- `use_cache` 是否使用缓存，如果`work_dir`下已存在部分评测数据可作为缓存使用。

### BaseStepPluginParam
[BaseStepPluginParam](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin_param.py) 继承自 [BasePluginParam](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/base_plugin_param.py)，是步骤插件参数的基类。


## 插件装饰器
插件装饰器 [plugins_decorator](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/plugins_decorator.py) 绑定了唯一的插件类型，为插件工厂识别并加载插件提供支持。

**内置装饰器**
```python
# 阶段插件装饰器
@DataProcessorPlugin    
@InferProcessorPlugin   
@MetricsProcessorPlugin 
@ReportProcessorPlugin  

# 步骤插件装饰器
@DataScenarioPlugin     
@DataAdapterPlugin      
@DataWindowServicePlugin
@InferLoadModelPlugin   
@InferAgentPlugin       
@MetricsPlugin          
@ReportPlugin           
```

## 插件工厂
插件工厂 [plugin_factory](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/plugin_factory.py) 负责插件的加载、缓存和实例化。

### PluginLoader
插件加载器，负责加载插件类并缓存已加载的插件类。

主要功能：

- 插件中心：记录每类插件对应的包路径以及默认的插件实现。
- 插件加载：根据插件类型在对应的包路径下搜索插件类，并缓存已加载的插件类避免重复加载。
- 依赖安装：自动安装已加载插件独有的依赖包。

### PluginFactory
插件工厂，负责根据插件类型和配置实例化插件对象，非单例模式，每次获取插件都会重新实例化插件对象。

主要功能：

- 插件加载：通过 `PluginLoader` 加载插件类。
- 获取插件：根据插件类型或插件名称获取插件类，解析运行参数并实例化插件对象。

## 插件实现

### 目录结构

```bash
agieval/
└── plugin/              # 插件实现
    ├── stage/           # 阶段插件
    │   ├── data/        # 数据处理阶段
    │   ├── infer/       # 推理处理阶段
    │   ├── metrics/     # 指标计算阶段
    │   └── report/      # 报告生成阶段
    ├── scenario/        # 数据处理-场景插件
    ├── adapter/         # 数据处理-适配器插件
    ├── model/           # 推理处理-模型插件
    ├── agent/           # 推理处理-智能体插件
    ├── metrics/         # 指标插件
    ├── report/          # 报告插件
    └── window_service/  # 数据处理-窗口服务插件
```

### 数据处理阶段
数据处理阶段负责数据的预处理、清洗和转换等操作，主要能力是屏蔽不同数据集的差异，提供一致的数据处理接口。处理步骤如下：

- `scenario` 核心步骤，用于加载数据集，输出统一的数据格式
- `adapter` 可选步骤，用于数据加工，输出prompt
- `window_service` 可选步骤，用于数据阶段，避免超过模型上下文长度


### 推理处理阶段
推理处理阶段负责处理每一个instance的推理结果，主要能力是屏蔽不同模型、框架的差异，提供一致推理接口。处理步骤如下：

- `model` 核心步骤，屏蔽模型差异，输入instance，输出推理结果
- `agent` 核心步骤，组装完整prompt，调用 `model` 插件获取推理结果

### 指标计算阶段
负责计算每个instance的指标，主要能力是聚合多种指标计算方式。处理步骤如下：

- `metrics` 计算特定的指标

### 报告生成阶段
负责生成评测报告，主要能力是统计分析评测结果。处理步骤如下：

- `report` 一种统计分析的方式