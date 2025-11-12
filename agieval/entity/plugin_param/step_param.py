from pydantic import Field

from agieval.core.plugin.base_plugin_param import BaseStepPluginParam


class BaseAdapterPluginParam(BaseStepPluginParam):
    max_new_tokens: int = Field(default=4096, description="Maximum generation length")
    temperature: float = Field(default=0.6, description="Sampling temperature")
    top_p: float = Field(default=0.95, description="Sampling top_p")
    top_k: int = Field(default=-1, description="Sampling top_k")
    presence_penalty: float | None = Field(default=None, description="Presence penalty")
    frequency_penalty: float | None = Field(default=None)
    stop_sequences: list = Field(default=[], description="Inference termination sequences")
   

class BaseAgentPluginParam(BaseStepPluginParam):
    disable_cache: bool = Field(default=False, description="Disable cache")
    pass

class BaseMetricsPluginParam(BaseStepPluginParam):
    metrics_name: str = Field(default="", description="Metric name")

class BaseModelPluginParam(BaseStepPluginParam):
    model: str = Field(default="", description="Model name")
    base_url: str = Field(default="", description="Model URL")
    api_key: str = Field(default="", description="Model api_key")
    retry_time: int = Field(default=10, description="Number of retries")
    retry_time_interval: int = Field(default=10, description="Retry interval time")
    custom_llm_provider: str = Field(default="openai", description="Custom llm_provider")

class BaseReportPluginParam(BaseStepPluginParam):
    pass

class BaseScenarioPluginParam(BaseStepPluginParam):
    benchmark_path: str = Field(default="", description="Dataset path (evaluation part)")

class BaseWindowServicePluginParam(BaseStepPluginParam):
    pass