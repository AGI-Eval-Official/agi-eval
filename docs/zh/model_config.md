# 模型准备

## 概述
框架目前仅支持通过API的方式调用模型服务，如有加载模型权重评测的需求，请自行适配插件使用。

## API模型
框架内置的模型代理插件都是依赖 `litellm` 组件调用模型服务, **要求被评测的模型能支持OpenAI的API协议**。

框架支持通过环境变量设置模型API，这样在发起评测任务时可以不指定模型参数。
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
或者在发起评测任务时指定模型参数来覆盖环境变量设置：
```bash
--plugin_param base_url=http://your-api-endpoint model=your-model-name api_key=your-api-key
```

## 权重模型
如果想使用权重模型评测，请自行部署模型服务。

如果部署的模型服务不能支持OpenAI协议，请按照 [插件开发指南](./component/plugin_guides.md#增加步骤插件) 适配 `load_model` 类型的插件使用。