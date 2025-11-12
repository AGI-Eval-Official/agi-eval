# Model Configuration

## Overview
The framework currently only supports calling model services through APIs. If you need to load model weights for evaluation, please adapt and use plugins yourself.

## API Models
The model agent plugins built into the framework all rely on the `litellm` component to call model services. **It is required that the model being evaluated supports the OpenAI API protocol**.

The framework supports setting model APIs through environment variables, so you don't need to specify model parameters when initiating evaluation tasks.
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
Or specify model parameters when initiating evaluation tasks to override environment variable settings:
```bash
--plugin_param base_url=http://your-api-endpoint model=your-model-name api_key=your-api-key
```

## Weight Models
If you want to use weight models for evaluation, please deploy model services yourself.

If the deployed model service cannot support the OpenAI protocol, please adapt `load_model` type plugins according to the [Plugin Development Guide](./component/plugin_guides.md#add-step-plugin) for use.
