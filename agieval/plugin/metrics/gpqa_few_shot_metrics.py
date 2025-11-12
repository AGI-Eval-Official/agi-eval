from pydantic import Field
from typing import List, Dict, Tuple
import re
import string
from agieval.common.constant import CORRECT_TAG
from agieval.core.plugin.plugins_decorator import MetricsPlugin
from agieval.entity.scenario_state import ScenarioState
from agieval.entity.stat import Stat, MetricName, PerInstanceStats
from agieval.entity.plugin_param.step_param import BaseMetricsPluginParam
from agieval.plugin.metrics.base_metrics import BaseMetrics


@MetricsPlugin
class GPQAFewShotMetrics(BaseMetrics[BaseMetricsPluginParam]):
    """
    Basic prefix matching metric calculation
    """

    @classmethod
    def get_metrics_name(cls) -> str:
        """
        return metrics_name
        """
        return "quasi_prefix_exact_match"

    def run(self, scenario_state: ScenarioState, aggregate_stats: List[Stat], per_instance_stats: List[PerInstanceStats]) -> Tuple[Stat, Dict[str, Stat]]:
        # Used to store current metric results, which will be merged into per_instance_stats later
        per_instance_stats_local = dict()
        aggregate_stat_local = Stat(MetricName(self.context_param.metrics_name))
        for request_state in scenario_state.request_states:
            # Get correct answers and model inference results
            golds = [reference for reference in request_state.instance.references if reference.is_correct]
            pred: str = request_state.result.completions[0].text.strip()

            # Calculate metrics
            qpem_score = max(self.compute(gold.output.text, pred) for gold in golds)
            stat = Stat(MetricName(self.context_param.metrics_name)).add(qpem_score)
            per_instance_stats_local[request_state.instance.id] = stat
            # Update aggregate_stat
            aggregate_stat_local.merge(stat)

        # # Merge current metrics into common per_instance_stats:
        # per_instance_stats = self.merge_per_instance_stat(per_instance_stats, per_instance_stats_local)
        # # Update aggregate_stat:
        # aggregate_stats = self.merge_aggregate_stats(aggregate_stats, aggregate_stat_local)
        return aggregate_stat_local, per_instance_stats_local

    def compute(self, gold, pred):
        return 1 if gold == self.parse_sampled_answer(pred) else 0

    def parse_sampled_answer(self, answer):
        LETTER_TO_INDEX = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
        patterns = [r'answer is \((.)\)', r'Answer: \((.)\)', r'answer: \((.)\)', r'answer \((.)\)', r'\((.)\)',
                    r'^([A-Za-z])$']
        for pattern in patterns:
            match = re.search(pattern, answer)
            if match and match.group(1) in LETTER_TO_INDEX:
                return match.group(1)
        return None
