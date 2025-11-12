from abc import abstractmethod
from typing import TypeVar

from agieval.core.plugin.base_plugin import BaseStep
from agieval.entity.plugin_param.step_param import BaseModelPluginParam
from agieval.entity.request import Request
from agieval.entity.request_result import RequestResult

T = TypeVar('T', bound=BaseModelPluginParam)
class BaseModel(BaseStep[T]):
    
    @abstractmethod
    def run(self, request: Request) -> RequestResult:
        pass

