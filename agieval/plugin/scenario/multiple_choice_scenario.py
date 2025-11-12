import json
from typing import List

from agieval.common.constant import CORRECT_TAG
from agieval.core.plugin.plugins_decorator import DataScenarioPlugin
from agieval.entity.instance import Instance, Input
from agieval.entity.plugin_param.step_param import BaseScenarioPluginParam
from agieval.entity.reference import Reference, Output
from agieval.plugin.scenario.base_scenario import BaseScenario


@DataScenarioPlugin
class MultipleChoiceScenario(BaseScenario[BaseScenarioPluginParam]):

    def run(self) -> List[Instance]:
        return self._load_instances()

    def _load_instances(self):
        with open(self.context_param.benchmark_path, 'r') as f:
            data = json.load(f)
        instances = []
        for idx, example in enumerate(data['examples']):
            instances.append(Instance(
                id=str(idx + 1),
                input=Input(text=example['input']),
                references=[
                    Reference(Output(text=target), tags=[CORRECT_TAG] if example["target_scores"][target] == 1 else [])
                    for target in example['target_scores'].keys()
                ],
                split='test'
            ))
        return instances
