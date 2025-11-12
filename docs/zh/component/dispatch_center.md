# 调度系统

## 概述

调度系统位于 [agieval/core/run](https://github.com/AGI-Eval-Official/agi-eval/tree/master/agieval/core/run) 目录下，负责评测任务的调度和执行管理，包含Dispatch和Runner两个主要模块，通过调度中心和执行器的协作实现灵活的任务调度。

## 目录结构

```bash
agieval/
└── core/
    └── run/             
        ├── dispatch_center.py
        ├── runner.py
        ├── runner_type.py
        ├── data_parallel/  # 数据并行调度
        └── local/          # 串行调度
```

### 核心类

#### DispatchCenter
`DispatchCenter` 是调度中心的抽象基类，负责任务调度和资源管理。

主要功能：

- 任务分发：将评测任务分发给不同的 Runner 执行
- 资源管理：管理子进程和共享资源
- 异常处理：处理执行过程中的异常和中断信号

#### Runner
`Runner` 是执行器的抽象基类，负责具体的任务执行。

## 开发指南

### DispatchCenter
1. 继承 [DispatchCenter](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/run/dispatch_center.py) 抽象类来自定义调度过程
2. 实现各抽象方法
    - `init_runners` 返回待实例化的Runner列表
    - `get_shared_param` 会在 **主进程** 中被调用，返回值将被序列化传入各Runner子进程，如有进程间共享数据需在此方法中定义
    - `restore_shared_param` 会在 **Runner子进程** 中被调用，接收 **get_shared_param** 方法的返回值
3. 【可选】定义与特定Runner的数据交互接口
4. [runner_type](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/run/runner_type.py) 中定义Runner类型
5. 修改 [DispatchCenter](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/run/dispatch_center.py) 的 **init** 方法，添加自定义 DispatchCenter

### Runner
1. 继承 [Runner](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/run/runner.py) 抽象类来自定义执行过程
2. 指定自定义 Runner 依赖的 DispatchCenter，用于数据交互
3. 实现抽象方法
    - `do_run` 执行具体任务


### 调度中心实现

自定义开发可参考以下实现

- `LocalDispatchCenter` 本地调度中心，用于单进程顺序执行。
- `DataParallelDispatchCenter` 数据并行调度中心，支持多进程并发执行。
- `DummyDispatchCenter` 虚拟调度中心，仅用于生成评测数据集配置。