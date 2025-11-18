# 🛠️ 环境准备

下面提供了 `agi-eval` 依赖环境的搭建过程、自定义数据集的要求、评测模型的要求。

我们强烈建议使用 `conda` 来管理您的 Python 环境。

## 虚拟环境（可选）
```bash
# Python版本: 要求 Python 3.11 或更高版本
conda create --name agieval python=3.11 -y
conda activate agieval
```

## 源码安装

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

- 可选依赖安装

以上安装了框架运行的必须依赖以及执行命令，框架核心的插件体系允许用户自定义插件实现，其必要依赖可作为框架的可选依赖放在插件依赖文件[requirements.json](https://github.com/AGI-Eval-Official/agi-eval/blob/master/agieval/plugin/requirements.json)中, 在对应插件第一次被加载使用的时候会自动安装。格式要求如下，文件内容是json格式，key为插件所在的module，value为依赖列表, 可指定版本与安装源。

```json
{
  "agieval.plugin.metrics.drop_f1_metrics": [  
      "scipy>=1.16.0 -i https://mirrors.aliyun.com/pypi/simple/"
  ]
}
```