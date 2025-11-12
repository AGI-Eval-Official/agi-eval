from agieval.entity.scenario_state import ScenarioState
from typing import Any


import os

from agieval.common.cache import Cache
from agieval.core.plugin.base_plugin import BasePlugin
from agieval.core.plugin.plugin_factory import PluginFactory
from agieval.core.run.runner_type import RunnerType
from agieval.entity.eval_config import EvalConfig
from agieval.entity.flow_config import ContextParam, PluginConfig, PluginType
from agieval.plugin.adapter.multi_choice_adapter import MultiChoiceAdapter
from agieval.plugin.scenario.base_scenario import DummyScenario
from agieval.plugin.scenario.multiple_choice_scenario import MultiChoiceScenario
from agieval.plugin.stage.data.data_processor import SimpleDataProcessor
from agieval.plugin.stage.infer.infer_processor import SimpleInferProcessor


def test_plugin_load():
    plugin_type = PluginFactory.find_plugin(plugin_type=PluginType.DATA_SCENARIO)
    assert plugin_type == PluginType.DATA_SCENARIO, "plugin type error"
    plugin = PluginFactory[BasePlugin].get_plugin_by_name(plugin_name="DummyScenario")
    assert plugin is not None, "plugin load error"
    assert isinstance(plugin, DummyScenario), "plugin load error"


def test_multi_choice_data_processor(tmp_path, tmp_multi_choice_dataset):
    work_dir = str(tmp_path)
    context_params = ContextParam(
        benchmark_id="tmp_multi_choice_dataset",
        benchmark_path=tmp_multi_choice_dataset,
        work_dir=work_dir
    )

    instances = MultiChoiceScenario(context_params).run()
    assert len(instances) == 1
    assert instances[0].id == "1"

    scenario_state = MultiChoiceAdapter(context_params).run(instances)
    assert len(scenario_state.request_states) == 1


    plugin_list = [
        PluginConfig(plugin_implement="MultiChoiceScenario", context_params=context_params),
        PluginConfig(plugin_implement="MultiChoiceAdapter", context_params=context_params),
        PluginConfig(plugin_implement="DummyWindowService", context_params=context_params)
    ]
    eval_config = EvalConfig(
        runner=RunnerType.DUMMY,
        eval_task_config="",
        work_dir=work_dir,
    )
    SimpleDataProcessor(context_params).run(plugin_list=plugin_list, eval_config=eval_config)
    result_path = Cache.get_result_path("tmp_multi_choice_dataset")
    assert set(os.listdir(result_path)) == set(["stats.json", "per_instance_stats.json", "scenario_state.json"])


def test_multi_choice_infer_processor(tmp_path, tmp_multi_choice_scenario_state):
    work_dir = str(tmp_path)
    context_params: dict[str, Any] = ContextParam(
        benchmark_id="tmp_multi_choice_dataset",
        work_dir=work_dir
    )
    plugin_list = [
        PluginConfig(plugin_implement="DummyModel", context_params=context_params),
        PluginConfig(plugin_implement="DummyAgent", context_params=context_params),
    ]
    eval_config = EvalConfig(
        runner=RunnerType.DUMMY,
        eval_task_config="",
        work_dir=work_dir,
    )
    SimpleInferProcessor(context_params).run(plugin_list=plugin_list, eval_config=eval_config)
    scenario_state: ScenarioState = Cache.load_scenario_state("tmp_multi_choice_dataset")
    assert len(scenario_state.request_states) == 1
    assert scenario_state.request_states[0].result is not None
    assert scenario_state.request_states[0].result.completions[0].text == "DummyAgent result"
