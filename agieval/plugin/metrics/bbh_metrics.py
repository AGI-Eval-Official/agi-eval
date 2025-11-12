import re
from pydantic import Field
from typing import List, Dict, Tuple

from agieval.core.plugin.plugins_decorator import MetricsPlugin
from agieval.entity.scenario_state import ScenarioState
from agieval.entity.reference import Reference
from agieval.entity.stat import Stat, MetricName, PerInstanceStats
from agieval.entity.plugin_param.step_param import BaseMetricsPluginParam
from agieval.plugin.metrics.base_metrics import BaseMetrics


def extract_last_answer(text):
    """
    Extract the final answer from BBH task output
    Supports two modes:
    1. "so the answer is X"
    2. "answer is X"
    """
    # First try to match the last "so the answer is"
    pattern_so = r'.*so the answer is\s*([^,\.]*)[,\.]'
    match_so = re.search(pattern_so, text, re.IGNORECASE)

    if match_so:
        result = match_so.group(1).strip()
        # Check if the result contains content in (?) format
        parentheses_pattern = r'\([A-Za-z]\)'
        parentheses_match = re.search(parentheses_pattern, result)
        if parentheses_match:
            return parentheses_match.group(0)
        return result

    # If "so the answer is" is not matched, try to match "answer is"
    pattern_answer = r'.*answer is\s*([^,\.]*)[,\.]'
    match_answer = re.search(pattern_answer, text, re.IGNORECASE)

    if match_answer:
        result = match_answer.group(1).strip()
        parentheses_pattern = r'\([A-Za-z]\)'
        parentheses_match = re.search(parentheses_pattern, result)
        if parentheses_match:
            return parentheses_match.group(0)
        return result

    return None


@MetricsPlugin
class BBHMetrics(BaseMetrics[BaseMetricsPluginParam]):
    """
    BBH (Big-Bench Hard) dataset metric calculation
    This metric extracts answers from model output and matches them with standard answers
    """

    @classmethod
    def get_metrics_name(cls) -> str:
        """
        return metrics_name
        """
        return "bbh_metrics"

    def run(self, scenario_state: ScenarioState, aggregate_stats: List[Stat], per_instance_stats: List[PerInstanceStats]) -> Tuple[Stat, Dict[str, Stat]]:
        # Used to store current metric results, which will be merged into per_instance_stats later
        per_instance_stats_local = dict()
        aggregate_stat_local = Stat(MetricName(self.context_param.metrics_name))
        for request_state in scenario_state.request_states:
            # Get correct answers and model inference results
            golds: List[Reference] = [
                reference for reference in request_state.instance.references if reference.is_correct]
            pred: str | None = request_state.result.completions[0].text.strip()
            target = golds[0].output.text
            score = 0
            pred = extract_last_answer(pred)
            if pred != None:
                pred = pred.replace(" ", "")
                target = target.replace(" ", "")
                if pred == target:
                    score = 1
                elif re.fullmatch(r'\([a-zA-Z]\)', pred):
                    pred = pred[1]
                    if pred == target:
                        score = 1
            stat = Stat(MetricName(self.context_param.metrics_name)).add(score)
            per_instance_stats_local[request_state.instance.id] = stat
            # Update aggregate_stat
            aggregate_stat_local.merge(stat)

        return aggregate_stat_local, per_instance_stats_local
