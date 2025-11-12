
from agieval.core.plugin.plugins_decorator import InferAgentPlugin
from agieval.entity.request_state import RequestState
from agieval.entity.plugin_param.step_param import BaseAgentPluginParam
from agieval.plugin.agent.base_agent import BaseAgent
from agieval.plugin.model.base_model import BaseModel


@InferAgentPlugin
class SingleRoundTextAgent(BaseAgent[BaseAgentPluginParam]):
    def run_one(self, model: BaseModel, request_state: RequestState) -> RequestState:
        request_result = model.run(request_state.request)
        request_state.result = request_result
        return request_state
