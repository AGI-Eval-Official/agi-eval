from agieval.core.run.runner_type import RunnerType
from agieval.entity.eval_config import EvalConfig
from agieval.entity.flow_config import BenchmarkConfig, ContextParam, FlowStage, PluginConfig
from agieval.entity.global_param import GlobalParam
from agieval.common.param_utils import load_model_api_config

eval_config: EvalConfig = EvalConfig(
    runner=RunnerType.DATA_PARALLEL,
    benchmark_config_template=True,
    dataset_files="example/dataset/test",
    benchmark_config="",
    flow_config_file="",
    work_dir="result/test",
    data_parallel=2,
    global_param=GlobalParam(),
    plugin_param=ContextParam(
        **load_model_api_config()
    )
)

benchmark_config_template = BenchmarkConfig(
    benchmark="",
    location_test="",
    use_cache=False,
    flow_config_file="",
    flow_stages=[
        FlowStage(
            plugin_implement="SimpleDataProcessor",
            plugins=[
                PluginConfig(
                    plugin_implement="MultipleChoiceScenario"
                )
            ]
        )
    ]
)