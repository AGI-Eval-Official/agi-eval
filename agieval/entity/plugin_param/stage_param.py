from pydantic import Field
from agieval.core.plugin.base_plugin_param import BaseStagePluginParam


class DataProcessorPluginParam(BaseStagePluginParam):
    pass
class InferProcessorPluginParam(BaseStagePluginParam):
    concurrency: int = Field(default=10, description="Concurrency")
    cache_update_interval: int = Field(default=10, description="Force update cache instance count interval, update cache after processing interval number of tasks")
    cache_update_time_interval: int = Field(default=30, description="Force update cache time interval, unit seconds (not precise control, ensure update frequency greater than current interval)")
class MetricsProcessorPluginParam(BaseStagePluginParam):
    pass
class ReportProcessorPluginParam(BaseStagePluginParam):
    pass
