# 🛠️ Environment Setup

The following provides the setup process for the **AGI-Eval** dependency environment, requirements for custom datasets, and requirements for evaluation models.

We strongly recommend using `conda` to manage your Python environment.

## Virtual Environment (optional)
```bash
# Python version: Requires Python 3.11 or higher
conda create --name agieval python=3.11 -y
conda activate agieval
```

## Source Installation

- Download source code
```bash
git clone https://github.com/AGI-Eval-Official/agi-eval.git
```

- Install dependencies
```bash
cd agi-eval

# Install Native backend
pip install -e .
```

- Optional dependency installation

The above installs the necessary dependencies for framework operation and execution commands. The core plugin system of the framework allows users to customize plugin implementations. Their necessary dependencies can be placed as optional dependencies of the framework in the plugin dependency file [requirements.json](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/plugin/requirements.json) and will be automatically installed when the corresponding plugin is first loaded and used. The format requirements are as follows: the file content is in JSON format, the key is the module where the plugin is located, and the value is the dependency list, where you can specify versions and installation sources.

```json
{
  "agieval.plugin.metrics.drop_f1_metrics": [
      "scipy>=1.16.0 -i https://mirrors.aliyun.com/pypi/simple/"
  ]
}
