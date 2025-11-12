from typing import TypeVar, List
from abc import abstractmethod

from agieval.core.plugin.base_plugin import BaseStep
from agieval.entity.instance import Instance
from agieval.entity.scenario_state import ScenarioState
from agieval.entity.plugin_param.step_param import BaseAdapterPluginParam

T = TypeVar('T', bound=BaseAdapterPluginParam)
class BaseAdapter(BaseStep[T]):

    @abstractmethod
    def run(self, instances: List[Instance]) -> ScenarioState:
        pass