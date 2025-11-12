from typing import List, TypeVar
from abc import abstractmethod

from agieval.core.plugin.base_plugin import BaseStep
from agieval.entity.instance import Instance
from agieval.entity.plugin_param.step_param import BaseScenarioPluginParam

T = TypeVar('T', bound=BaseScenarioPluginParam)
class BaseScenario(BaseStep[T]):
    
    @abstractmethod
    def run(self) -> List[Instance]:
        pass