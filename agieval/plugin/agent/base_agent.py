from abc import abstractmethod
from typing import TypeVar

from agieval.core.plugin.base_plugin import BaseStep
from agieval.entity.request_state import RequestState
from agieval.entity.plugin_param.step_param import BaseAgentPluginParam
from agieval.plugin.model.base_model import BaseModel

T = TypeVar('T', bound=BaseAgentPluginParam)
class BaseAgent(BaseStep[T]):

    def run(self, model: BaseModel, request_state: RequestState) -> RequestState:
        if not self.context_param.disable_cache:
            if request_state.result is not None:
                request_state.cached = True
                return request_state
        return self.run_one(model, request_state)
    
    @abstractmethod
    def run_one(self, model: BaseModel, request_state: RequestState) -> RequestState:
        pass
