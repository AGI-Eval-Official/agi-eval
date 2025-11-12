from pydantic import BaseModel, Field

from agieval.core.run.runner_type import RunnerType
from agieval.entity.global_param import GlobalParam

class EvalConfig(BaseModel):
    
    debug: bool = Field(default=False)
    runner: RunnerType 
    benchmark_config_template: bool = Field(default=False)
    dataset_files: str = Field(default="")
    benchmark_config: str = Field(default="")
    flow_config_file: str = Field(default="")
    work_dir: str
    data_parallel: int = Field(default=1)

    global_param: GlobalParam = Field(default_factory=GlobalParam)
    plugin_param: dict = Field(default_factory=dict)
