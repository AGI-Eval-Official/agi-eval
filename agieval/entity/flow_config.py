from enum import Enum
from typing import TypeAlias, Any
from pydantic import BaseModel, Field


class PluginType(str, Enum):
    NONE_TYPE = "none_type"
    # Evaluation stage
    STAGE_DATA_PROCESSOR = "stage_data_processor"
    STAGE_INFER_PROCESSOR = "stage_infer_processor"
    STAGE_METRICS_PROCESSOR = "stage_metrics_processor"
    STAGE_REPORT_PROCESSOR = "stage_report_processor"


    # Replaceable execution steps under each stage
    DATA_SCENARIO = "scenario"
    DATA_ADAPTER = "adapter"
    DATA_WINDOW_SERVICE = "window_service"

    INFER_LOAD_MODEL = "load_model"
    INFER_AGENT = "agent"

    METRICS = "metrics"
    
    REPORT = "report"



ContextParam: TypeAlias = dict[str, Any]


class PluginConfig(BaseModel):
    plugin_implement: str = Field(default="")
    plugin_type: PluginType = Field(default=PluginType.NONE_TYPE)
    context_params: ContextParam = Field(default_factory=dict)


class FlowStage(BaseModel):
    stage: str = Field(default="")
    plugin_type: PluginType = Field(default=PluginType.NONE_TYPE)
    plugin_implement: str
    context_params: ContextParam = Field(default_factory=dict)
    plugins: list[PluginConfig] = Field(default_factory=list)
    use_cache: bool = Field(default=True)


class BenchmarkConfig(BaseModel):
    benchmark: str
    location_test: str
    flow_stages: list[FlowStage] = Field(default=[])
    flow_config_file: str = Field(default="")
    use_cache: bool = Field(default=True)
