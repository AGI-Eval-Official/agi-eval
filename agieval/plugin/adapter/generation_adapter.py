from typing import List

from agieval.core.plugin.plugins_decorator import DataAdapterPlugin
from agieval.entity.instance import Instance
from agieval.entity.request import Message, Request
from agieval.entity.scenario_state import ScenarioState
from agieval.entity.request_state import RequestState
from agieval.entity.plugin_param.step_param import BaseAdapterPluginParam
from agieval.plugin.adapter.base_adapter import BaseAdapter


@DataAdapterPlugin
class GenerationAdapter(BaseAdapter[BaseAdapterPluginParam]):

    def run(self, instances: List[Instance]) -> ScenarioState:
        all_request_states: List[RequestState] = [self.generate_requests(instance) for instance in instances]
        return ScenarioState(all_request_states)

    def generate_requests(self, eval_instance: Instance) -> RequestState:
        request = Request(
            messages=[Message(role="user", content=eval_instance.input.text)],
            temperature=self.context_param.temperature,
            max_new_tokens=self.context_param.max_new_tokens,
            stop_sequences=self.context_param.stop_sequences,
            top_p=self.context_param.top_p,
            top_k=self.context_param.top_k,
            frequency_penalty=self.context_param.frequency_penalty,
            presence_penalty=self.context_param.presence_penalty
        )
        request_state = RequestState(
            instance=eval_instance,
            output_mapping=None,
            request=request,
            result=None,
        )
        return request_state
