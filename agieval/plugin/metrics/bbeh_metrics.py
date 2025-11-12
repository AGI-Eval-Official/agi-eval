import string
from pydantic import Field
from typing import List, Dict, Tuple

from agieval.core.plugin.plugins_decorator import MetricsPlugin
from agieval.entity.scenario_state import ScenarioState
from agieval.entity.reference import Reference
from agieval.entity.stat import Stat, MetricName, PerInstanceStats
from agieval.entity.plugin_param.step_param import BaseMetricsPluginParam
from agieval.plugin.metrics.base_metrics import BaseMetrics


def compare_score(answer_text, label):
    # Define possible prefixes
    prefixes = [
        "The answer is: ", 
        "The answer is ", 
        "The final answer is: ", 
        "The final answer is "
    ]
    
    # Try to find and extract the answer
    final_answer = None
    for prefix in prefixes:
        if prefix in answer_text:
            final_answer = answer_text.split(prefix)[1]
            break
    
    if final_answer is None:
        return 0
    
    # Remove wrapper text such as boxed, text, texttt or **
    import re
    final_answer = re.sub(r'boxed|text|texttt|\*\*', '', final_answer).strip()
    
    # Remove line breaks and subsequent text
    final_answer = final_answer.split("\n")[0]
    
    final_answer = final_answer.lower()
    label = label.lower()
    
    # Perform answer correctness judgment
    # Rule 1: If the answer and label are exactly the same
    if final_answer == label:
        return 1
    
    # Rule 2: Compare after removing single quotes, double quotes or parentheses
    stripped_final_answer = final_answer.strip("'\"()")
    stripped_label = label.strip("'\"()")
    if stripped_final_answer == stripped_label:
        return 1
    
    # Rule 2.1: Remove trailing whitespace and punctuation from the string
    stripped_final_answer = final_answer.rstrip(string.whitespace + string.punctuation)
    stripped_label = label.rstrip(string.whitespace + string.punctuation)
    if stripped_final_answer == stripped_label:
        return 1
    
    # Rule 3: For multiple choice questions, the answer may only have letters without parentheses
    if label.startswith("(") and label.endswith(")"):
        if final_answer == label[1]:
            return 1
    
    # Rule 4: Handle multi-element answers
    if ',' in label:
        label_parts = [part.strip() for part in label.split(',')]
        answer_parts = [part.strip() for part in final_answer.split(',')]
        if label_parts == answer_parts:
            return 1
    
    # If no correct answer is matched, return the original answer
    return 0

@MetricsPlugin
class BBEHMetrics(BaseMetrics[BaseMetricsPluginParam]):
    """
    BBEH Normative Metrics
    """

    @classmethod
    def get_metrics_name(cls) -> str:
        """
        return metrics_name
        """
        return "bbeh_metrics"

    def run(self, scenario_state: ScenarioState, aggregate_stats: List[Stat], per_instance_stats: List[PerInstanceStats]) -> Tuple[Stat, Dict[str, Stat]]:
        # Used to store current metric results, which will be merged into per_instance_stats later
        per_instance_stats_local = dict()
        aggregate_stat_local = Stat(MetricName(self.context_param.metrics_name))
        for request_state in scenario_state.request_states:
            # Get correct answers and model inference results
            golds: List[Reference] = [reference for reference in request_state.instance.references if reference.is_correct]
            pred: str = request_state.result.completions[0].text.strip()
            answer_text = str(pred)
            label = str(golds[0].output.text)
            score = compare_score(answer_text,label)
            stat = Stat(MetricName(self.context_param.metrics_name)).add(score)
            per_instance_stats_local[request_state.instance.id] = stat
            # Update aggregate_stat
            aggregate_stat_local.merge(stat)

        return aggregate_stat_local, per_instance_stats_local

