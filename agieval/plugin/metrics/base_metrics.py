import time
from typing import List, TypeVar, Dict, Tuple
from abc import abstractmethod
import string
import re

from agieval.core.plugin.base_plugin import BaseStep
from agieval.entity.scenario_state import ScenarioState
from agieval.entity.stat import Stat, PerInstanceStats
from agieval.entity.plugin_param.step_param import BaseMetricsPluginParam

T = TypeVar('T', bound=BaseMetricsPluginParam)
class BaseMetrics(BaseStep[T]):

    @classmethod
    def get_metrics_name(cls) -> str:
        '''
        return metrics_name
        '''
        return f"mock_metrics_name_{int(time.time())}"


    @abstractmethod
    def run(self, scenario_state: ScenarioState, aggregate_stats: List[Stat], per_instance_stats: List[PerInstanceStats]) -> Tuple[Stat, Dict[str, Stat]]:
        pass
    

    def normalize_text(self, text: str) -> str:
        """Lower text and remove punctuation, articles and extra whitespace.
        Copied from the [QuAC](http://quac.ai/) evaluation script found at
        https://s3.amazonaws.com/my89public/quac/scorer.py"""

        def remove_articles(text: str) -> str:
            return re.sub(r"\b(a|an|the)\b", " ", text)

        def white_space_fix(text: str) -> str:
            return " ".join(text.split())

        def remove_punc(text: str) -> str:
            exclude = set(string.punctuation)
            return "".join(ch for ch in text if ch not in exclude)

        def lower(text: str) -> str:
            return text.lower()

        return white_space_fix(remove_punc(lower(text)))