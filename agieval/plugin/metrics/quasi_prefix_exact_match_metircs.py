from pydantic import Field
from typing import List, Dict, Tuple
import re
import string

from agieval.core.plugin.plugins_decorator import MetricsPlugin
from agieval.entity.scenario_state import ScenarioState
from agieval.entity.stat import Stat, MetricName, PerInstanceStats
from agieval.entity.plugin_param.step_param import BaseMetricsPluginParam
from agieval.plugin.metrics.base_metrics import BaseMetrics
from agieval.entity.reference import Reference


@MetricsPlugin
class QuasiPrefixExactMatchMetrics(BaseMetrics[BaseMetricsPluginParam]):
    @classmethod
    def get_metrics_name(cls) -> str:
        """
        return metrics_name
        """
        return "quasi_prefix_exact_match"

    def run(self, scenario_state: ScenarioState, aggregate_stats: List[Stat],
            per_instance_stats: List[PerInstanceStats]) -> Tuple[Stat, Dict[str, Stat]]:
        # Used to store current metric results, which will be merged into per_instance_stats later
        per_instance_stats_local = dict()
        aggregate_stat_local = Stat(
            MetricName(self.context_param.metrics_name))
        for request_state in scenario_state.request_states:
            # Get correct answers and model inference results
            golds: List[Reference] = [
                reference for reference in request_state.instance.references if reference.is_correct]
            if len(golds) == 0:
                self.log_error(
                    f"Data anomaly: There is data without correct answers. id: {request_state.instance.id} request_state: {request_state}")
            if request_state.result is None:
                pred = ""
            else:
                pred: str = request_state.result.completions[0].text.strip()
            # For multiple choice questions, answer mapping needs to be processed
            if request_state.output_mapping is not None:
                pred = self.fetch_mapping(pred, request_state.output_mapping)
                # For multiple choice questions, since the text is mapped back to options and is fixed, we use exact matching instead of prefix matching to prevent misjudgment of similar answers (e.g., 1 and 10, 128 and -128)
                qpem_score = max(self.exact_match(
                    gold.output.text, pred) for gold in golds)

            else:
                # Calculate prefix matching metrics
                qpem_score = max(self.quasi_prefix_exact_match(
                    gold.output.text, pred) for gold in golds)
            stat = Stat(MetricName(self.context_param.metrics_name)
                        ).add(qpem_score)
            per_instance_stats_local[request_state.instance.id] = stat
            # Update aggregate_stat
            aggregate_stat_local.merge(stat)

        return aggregate_stat_local, per_instance_stats_local

    def quasi_prefix_exact_match(self, gold: str, pred: str) -> float:
        if not pred or not gold:
            return 0

        return 1 if self.normalize_text(pred).startswith(self.normalize_text(gold)) else 0

    def exact_match(self, gold: str, pred: str) -> float:
        if not pred or not gold:
            return 0

        return 1 if pred == gold else 0

    def fetch_mapping(self, pred, output_mapping):
        if pred in output_mapping:
            return output_mapping.get(pred)
        for l in range(len(pred), 0, -1):
            if pred[:l] in output_mapping:
                return output_mapping.get(pred[:l])
        return pred
