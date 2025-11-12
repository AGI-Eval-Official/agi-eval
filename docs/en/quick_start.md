# Quick Start

## Overview
This section introduces how to initiate an evaluation task.


## 🛠️ Environment Setup
For details, refer to [Environment Setup](./installation.md). After the environment setup is completed, you can use the framework capabilities through the command line tool `agieval`. For detailed introduction, refer to [Command Line Tool](./agieval_cli.md).

### 💻 Environment Setup

We strongly recommend using `conda` to manage your Python environment.

#### Virtual Environment (optional)
  ```bash
  # Python version: Requires Python 3.11 or higher
  conda create --name agieval python=3.11 -y
  conda activate agieval
  ```

#### Source Installation
- Download source code
```bash
git clone git@github.com:AGI-Eval-Official/agi-eval.git
```
- Install dependencies
```bash
cd agi-eval

# Install Native backend
pip install -e .
```

## 📚 Data Preparation
The framework has adapted some public datasets that can be used directly. You can view the list of supported datasets through the `agieval benchmarks` command. When evaluating these datasets for the first time, data files will be automatically downloaded to the local `datasets` directory. For detailed instructions, refer to [Public Datasets](./common_dataset.md).

If you have new datasets to evaluate, refer to [Dataset Adaptation](./custom_dataset.md).

## 🧠 Model Preparation
refer to [Model Configuration](./model_config.md) to ensure you have callable model APIs.

#### API Models
Currently, only supports evaluation through `litellm` calling APIs, so you need to provide model services that support the OpenAI API protocol. If the model being evaluated already has deployed model services that support the OpenAI API protocol, you can use them directly. Execute the following commands to configure model parameters:
```shell
# Model to be evaluated
export API_BASE_URL=http://your-api-endpoint
export MODEL_NAME=your-model-name
export API_KEY=your-api-key

# Scoring model
export SCORE_API_BASE_URL=http://your-api-endpoint
export SCORE_MODEL_NAME=your-model-name
export SCORE_API_KEY=your-api-key
```

## 🏗️ ️Start Evaluation
Execute the `agieval start test` command to start the evaluation task.

For more detailed introduction to starting evaluation tasks, refer to [Start Evaluation](./start_task.md).

## 📈 Evaluation Results
Start the evaluation result visualization service through the `agieval appstart --result_dir=result/test` command to view the evaluation process and results. For details, refer to [Evaluation Results](./eval_result.md).


## More

Click the following links to learn more about the framework details.

- [Framework Overview](./framework_overview.md)
- [Dispatch Center](./component/dispatch_center.md)
- [Plugin System](./component/plugin_system.md)
- [Configuration Management](./component/config_manager.md)
- [Plugin Development Guide](./component/plugin_guides.md)
- [Public Datasets](./common_dataset.md)
