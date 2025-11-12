from typing import TypeVar, List

from agieval.core.plugin.base_plugin import BaseStage
from agieval.core.plugin.plugins_decorator import DataProcessorPlugin
from agieval.core.plugin.plugin_factory import PluginFactory
from agieval.plugin.scenario.base_scenario import BaseScenario
from agieval.plugin.adapter.base_adapter import BaseAdapter
from agieval.plugin.window_service.base_window_service import BaseWindowService
from agieval.entity.scenario_state import ScenarioState
from agieval.entity.flow_config import PluginType
from agieval.entity.plugin_param.stage_param import DataProcessorPluginParam
from agieval.common.cache import Cache

T = TypeVar('T', bound=DataProcessorPluginParam)
class DataProcessor(BaseStage[T]):

    def cache_is_available(self) -> bool:
        scenario_state: ScenarioState = Cache.load_scenario_state(self.context_param.benchmark_id)
        return scenario_state is not None and len(scenario_state.request_states) > 0


    @staticmethod
    def get_steps() -> List[PluginType]:
        return [PluginType.DATA_SCENARIO, PluginType.DATA_ADAPTER, PluginType.DATA_WINDOW_SERVICE]


@DataProcessorPlugin
class SimpleDataProcessor(DataProcessor[DataProcessorPluginParam]):
    
    def process(self):
        data_scenario = PluginFactory[BaseScenario].get_plugin_by_type(plugin_type=PluginType.DATA_SCENARIO)
        instances = data_scenario.run()

        data_adapter = PluginFactory[BaseAdapter].get_plugin_by_type(PluginType.DATA_ADAPTER)
        scenario_state = data_adapter.run(instances)

        data_window_service  = PluginFactory[BaseWindowService].get_plugin_by_type(PluginType.DATA_WINDOW_SERVICE)
        scenario_state = data_window_service.run(scenario_state)


        Cache.save_stats([], self.context_param.benchmark_id)
        Cache.save_per_instance_stat([], self.context_param.benchmark_id)
        Cache.save_scenario_state(scenario_state, self.context_param.benchmark_id)
