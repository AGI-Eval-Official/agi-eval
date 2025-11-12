from typing import TypeVar
from abc import abstractmethod


from agieval.core.plugin.base_plugin import BaseStep
from agieval.core.plugin.plugins_decorator import DataWindowServicePlugin
from agieval.entity.scenario_state import ScenarioState
from agieval.entity.plugin_param.step_param import BaseWindowServicePluginParam

T = TypeVar('T', bound=BaseWindowServicePluginParam)
class BaseWindowService(BaseStep[T]):
    
    @abstractmethod
    def run(self, scenario_state: ScenarioState) -> ScenarioState:
        pass


@DataWindowServicePlugin
class GenerationWindowService(BaseWindowService[BaseWindowServicePluginParam]):
    """
    WindowService is deprecated, only for compatibility.
    """
    def run(self, scenario_state: ScenarioState) -> ScenarioState:
        self.log(f"GenerationWindowService run, {self.context_param}")
        return scenario_state