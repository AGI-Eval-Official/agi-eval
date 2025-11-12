# Framework Overview

## Introduction

AGI-Eval is a plugin-based architecture evaluation framework for Large Language Models (LLMs), aiming to provide a flexible and scalable evaluation platform. The framework supports multiple evaluation scenarios, model integration methods, and evaluation metrics, adopting a modular design to facilitate developers in customizing and extending functionality according to their needs.

## Core Features

### 🔧 Plugin Architecture
- **Extensible Design**: Supports custom data processing, model inference, metric calculation, and report generation plugins
- **Modular Components**: Each functional module can be independently developed and replaced
- **Standardized Interfaces**: Unified plugin interface specifications for third-party extensions

### 🚀 Multiple Running Modes
- **Single Machine Mode**: Suitable for debugging and small-scale evaluation
- **Data Parallel**: Supports multi-process parallel processing to improve large-scale evaluation efficiency
- **Flexible Scheduling**: Dynamically adjust concurrency based on resource availability

### ⚙️ Flexible Configuration
- **Template Configuration**: Supports configuration templates for batch dataset evaluation
- **Dynamic Parameters**: Supports runtime parameter passing and overriding
- **Multi-layer Configuration**: Hierarchical management of global parameters and plugin parameters

### 📊 Visualization Reports
- **Web Interface**: Provides intuitive evaluation result display
- **Multi-dimensional Analysis**: Supports metric statistics, detail viewing, and parameter comparison

## Core Components

### Dispatch Center
The dispatch center is responsible for the distribution and execution management of evaluation tasks. Multiple parallel Runner task executors obtain tasks from a process-shared task queue and execute them.

Main responsibilities:

- **Task Scheduling**: Responsible for the distribution and execution management of evaluation tasks
- **Resource Management**: Manage computing resources and concurrency control

### Plugin System
The plugin system is the core of the framework, adopting a plugin-based design to support flexible extension.

Main functions:

- **Plugin Registration**: Automatic discovery and registration of plugins
- **Lifecycle Management**: Manage plugin initialization, execution, and cleanup
- **Parameter Passing**: Handle parameter passing and context sharing between plugins

### Configuration Manager
The configuration management module is responsible for parsing and validating configuration files, handling merging and overriding of multi-layer configurations.

Main functions:

- **Configuration Parsing**: Parse and validate configuration files
- **Parameter Merging**: Handle merging and overriding of multi-layer configurations
- **Template Rendering**: Support dynamic rendering of configuration templates

## Framework Structure

```bash
agieval/
├── cli/                 # Command Line Interface
├── common/              # Common utilities and components
├── core/                # Core framework code
│   ├── plugin/          # Plugin system core
│   └── run/             # Runtime scheduling system
├── entity/              # Data entities and configuration definitions
├── plugin/              # Plugin implementations
└── visualization/       # Visualization reports
```

## Next Steps

Please refer to the following documents for detailed information about each module:

- [Dispatch Center](./component/dispatch_center.md)
- [Plugin System](./component/plugin_system.md)
- [Configuration Management](./component/config_manager.md)
