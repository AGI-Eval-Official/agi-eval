# 插件开发指南

## 概述
如果有需求适配新的公开数据集或者自定义数据集，亦或是有自定义的评测指标计算的需求，都需要定制化实现对应的插件来支持，本节将详细介绍如何从零开始实现一个完整的插件。

## 目录结构

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

## 步骤插件
首先要明确开发`阶段插件`还是`步骤插件`，一般情况下只需要开发`步骤插件`实现如数据格式转换、模型调用、指标计算等特定功能即可。

### 增加步骤类型
首先判断框架内置的各类步骤插件是否能够符合需求，如果要实现的功能在内置步骤的能力覆盖范围内则可直接查看下一步 [增加步骤插件](#增加步骤插件)。否则可以按下述方式定义一个新的步骤类型，之后再增加步骤插件。

1. `定义插件类型` 在 [PluginType](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/flow_config.py) 中新增插件类型枚举。
```python
class PluginType(str, Enum):
    ...
    # 新增插件类型
    CUSTOM = "custom"
```

2. `定义参数类` 在 [step_param](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/plugin_param/step_param.py) 中新增参数基类
```python
class BaseCustomPluginParam(BaseStepPluginParam):  # 必须继承自步骤插件参数基类 BaseStepPluginParam
    pass  # 定义参数字段
```

3. `定义步骤插件基类` 在 [agieval/plugin](https://github.com/AGI-Eval-Official/agi-eval/tree/master/agieval/plugin) 下增加新类型插件的包路径， 然后定义步骤插件基类。
```python
# 在包路径 agieval/plugin/custom 下增加插件文件  base_custom.py

from abc import abstractmethod
from typing import TypeVar
from agieval.core.plugin.base_plugin import BaseStep
from agieval.entity.plugin_param.step_param import BaseCustomPluginParam

T = TypeVar('T', bound=BaseCustomPluginParam)  # 定义参数泛型
class BaseCustom(BaseStep[T]):   # 必须继承自步骤插件基类 BaseStep
    
    @abstractmethod    # 必须实现 run 方法，入参、出参可自定义
    def run(self):
        pass
```

4. `增加插件装饰器` 在 [plugins_decorator](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/plugins_decorator.py) 中新增插件装饰器。
```python
CustomPlugin = create_plugin_decorator(PluginType.CUSTOM, "CustomPlugin") # 基类 BaseCustom，  记录下插件类型的基类
```



### 增加步骤插件
定义一个步骤插件的过程很简单：

1. 查看 [plugins_decorator.py](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/plugin/plugins_decorator.py) 文件，根据要开发的插件类型确定插件装饰器。
2. 继承步骤类型对应的步骤插件基类。
3. 指定步骤插件的参数类（可新增）。

```python
# 定义插件参数类（可选）
class BaseCustomParam(BaseCustomPluginParam):
    param: str = Field(default="", description="参数描述")

# 定义步骤插件
@CustomPlugin   # 必须使用插件装饰器
class DummyModel(BaseCustom[BaseCustomParam]):  # 继承Custom类型的步骤插件基类

    def run(self):  # 实现run方法
        pass
```


## 阶段插件
> 阶段插件和步骤插件本质上没有区别，只是需要继承的基类不同。

阶段插件的能力是由多个步骤插件组合实现，所以首先要明确具体的执行步骤，然后按 [步骤插件](#步骤插件) 所述先开发步骤插件，最后再将步骤插件组合成阶段插件。

### 增加阶段类型
开发过程与 [增加步骤类型](#增加步骤类型) 一致，只需要改变继承的基类即可。

- `参数类与装饰器` 需要在 [stage_param](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/entity/plugin_param/stage_param.py) 中新增参数基类
```python
class CustomProcessorPluginParam(BaseStagePluginParam):  # 必须继承自阶段插件参数基类 BaseStagePluginParam
    pass  # 定义参数字段

# 增加装饰器
CustomProcessorPlugin = create_plugin_decorator(PluginType.CUSTOM, "CustomProcessorPlugin")
```

- `阶段插件基类` 在 [agieval/plugin/stage](https://github.com/AGI-Eval-Official/agi-eval/tree/master/agieval/plugin/stage) 下增加阶段插件包路径，然后定义阶段插件基类。
```python
T = TypeVar('T', bound=CustomProcessorPluginParam)
class CustomProcessor(BaseStage[T]):
    # 必须实现 cache_is_available 方法，判断缓存数据是否可用
    def cache_is_available(self) -> bool:
        return False

    # 必须实现 get_steps 方法，返回这个阶段的处理步骤类型集合
    @staticmethod
    def get_steps() -> List[PluginType]:
        return [PluginType.CUSTOM]
```

### 增加阶段插件
```python
# 定义插件参数类（可选）
class CustomProcessorParam(BaseCustomPluginParam):
    param: str = Field(default="", description="参数描述")

@CustomProcessorPlugin
class SimpleCustomProcessor(CustomProcessor[CustomProcessorParam]):

    # 必须实现process方法进程功能开发
    def process(self, plugin_list: List[PluginConfig], eval_config: EvalConfig):
        pass
        # 可以参考内置插件的实现，通过 PluginFactory 获取步骤插件实例使用
```