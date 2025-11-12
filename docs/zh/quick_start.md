# 快速开始

## 概述
本节将介绍如何发起一个评测任务。 


## 🛠️ 环境准备
详情查看 [环境准备](./installation.md)，环境准备安装完成之后，可通过命令行工具 `agieval` 使用框架能力。详细介绍查看 [命令行工具](./agieval_cli.md)。

### 💻 环境搭建

我们强烈建议使用 `conda` 来管理您的 Python 环境。

#### 虚拟环境（可选）
  ```bash
  # Python版本: 要求 Python 3.11 或更高版本
  conda create --name agieval python=3.11 -y
  conda activate agieval
  ```

#### 源码安装
- 下载源码
```bash
git clone https://github.com/AGI-Eval-Official/agi-eval.git
```
- 依赖安装
```bash
cd agi-eval

# 安装 Native backend
pip install -e .  
```

## 📚 数据准备
框架已适配了部分公开数据集可直接使用，通过 `agieval benchmarks` 命令查看支持的数据集列表，首次评测这些数据集会自动下载数据文件到本地`datasets`目录下。 详细说明查看 [公开数据集](./common_dataset.md)。

如果有新的数据集要评测，查看 [数据集适配](./custom_dataset.md)。

## 🧠 模型准备
查看 [模型准备](./model_config.md) 确保有可调用的模型API。

#### API模型
目前仅支持通过`litellm`调用API进行评测, 所以需要提供支持OpenAI API协议的模型服务。如果评测的模型已部署有支持OpenAI API协议的模型服务可以直接使用。执行以下命令配置模型参数:
```shell
# 待评测模型
export API_BASE_URL=http://your-api-endpoint
export MODEL_NAME=your-model-name
export API_KEY=your-api-key

# 打分模型
export SCORE_API_BASE_URL=http://your-api-endpoint
export SCORE_MODEL_NAME=your-model-name
export SCORE_API_KEY=your-api-key
```

## 🏗️ ️开始评测
执行 `agieval start test` 命令启动评测任务。

启动评测任务的更详细介绍查看 [开始评测](./start_task.md)。

## 📈 评测结果
通过 `agieval appstart --result_dir=result/test` 命令启动评测结果可视化服务，查看评测过程及结果。详情查看 [评测结果](./eval_result.md)。


## 更多

点击以下链接了解框架更多的细节。

- [框架介绍](./framework_overview.md)
- [调度中心](./component/dispatch_center.md)
- [插件系统](./component/plugin_system.md)
- [配置管理](./component/config_manager.md)
- [插件开发指南](./component/plugin_guides.md)
- [公开数据集](./common_dataset.md)


