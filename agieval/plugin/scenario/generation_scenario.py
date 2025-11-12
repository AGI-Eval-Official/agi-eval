import json
from typing import List

from agieval.common.constant import CORRECT_TAG
from agieval.core.plugin.plugins_decorator import DataScenarioPlugin
from agieval.entity.instance import Instance, Input
from agieval.entity.plugin_param.step_param import BaseScenarioPluginParam
from agieval.entity.reference import Reference, Output
from agieval.plugin.scenario.base_scenario import BaseScenario


@DataScenarioPlugin
class GenerationScenario(BaseScenario[BaseScenarioPluginParam]):


    def run(self) -> List[Instance]:
        """Load dataset and return Instance list"""
        self.log(f"Start loading dataset: {self.context_param.benchmark_path}")
        instances = self._load_instances()
        self.log(f"Successfully loaded {len(instances)} data entries")
        return instances

    def _load_instances(self) -> List[Instance]:
        """Load data from JSON file"""
        # Read JSON file
        with open(self.context_param.benchmark_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        instances = []

        # Parse examples
        for idx, example in enumerate(data['examples']):
            # Support target as single value or list
            if isinstance(example.get('target'), list):
                # Multiple correct answers
                references = [
                    Reference(Output(text=str(target)), tags=[CORRECT_TAG])
                    for target in example['target']
                ]
            else:
                # Single correct answer
                references = [
                    Reference(
                        Output(text=str(example['target'])), tags=[CORRECT_TAG])
                ]

            instances.append(Instance(
                id=str(idx),
                input=Input(text=example['input']),
                references=references,
                split='test'
            ))
        return instances
