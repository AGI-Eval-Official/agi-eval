# Dispatch System

## Overview

The dispatch system is located in the [agieval/core/run](https://github.com/AGI-Eval-Official/agi-eval/tree/master/agieval/core/run) directory, responsible for task scheduling and execution management of evaluation tasks. It contains two main modules, Dispatch and Runner, and implements flexible task scheduling through the collaboration of the dispatch center and executors.

## Directory Structure

```bash
agieval/
└── core/
    └── run/
        ├── dispatch_center.py
        ├── runner.py
        ├── runner_type.py
        ├── data_parallel/  # Data parallel scheduling
        └── local/          # Serial scheduling
```

### Core Classes

#### DispatchCenter
`DispatchCenter` is the abstract base class of the dispatch center, responsible for task scheduling and resource management.

Main functions:

- Task Distribution: Distribute evaluation tasks to different Runners for execution
- Resource Management: Manage subprocesses and shared resources
- Exception Handling: Handle exceptions and interrupt signals during execution

#### Runner
`Runner` is the abstract base class of executors, responsible for specific task execution.

## Development Guide

### DispatchCenter
1. Inherit the [DispatchCenter](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/run/dispatch_center.py) abstract class to customize the scheduling process
2. Implement abstract methods
    - `init_runners` Return the list of Runners to be instantiated
    - `get_shared_param` will be called in the **main process**, and the return value will be serialized and passed to each Runner subprocess. If there is inter-process shared data, it needs to be defined in this method
    - `restore_shared_param` will be called in **Runner subprocesses** to receive the return value of the **get_shared_param** method
3. [Optional] Define data interaction interfaces with specific Runners
4. Define Runner type in [runner_type](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/run/runner_type.py)
5. Modify the **init** method of [DispatchCenter](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/run/dispatch_center.py) to add custom DispatchCenter

### Runner
1. Inherit the [Runner](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/core/run/runner.py) abstract class to customize the execution process
2. Specify the DispatchCenter that the custom Runner depends on for data interaction
3. Implement abstract methods
    - `do_run` Execute specific tasks


### Dispatch Center Implementation

For custom development, you can refer to the following implementations

- `LocalDispatchCenter` Local dispatch center for single-process sequential execution.
- `DataParallelDispatchCenter` Data parallel dispatch center supporting multi-process concurrent execution.
- `DummyDispatchCenter` Virtual dispatch center, only used for generating evaluation dataset configurations.
