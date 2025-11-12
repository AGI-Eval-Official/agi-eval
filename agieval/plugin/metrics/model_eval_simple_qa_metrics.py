from pydantic import Field
from typing import List, Dict, Tuple
import re
from agieval.core.plugin.plugins_decorator import MetricsPlugin
from agieval.entity.scenario_state import ScenarioState, RequestState
from agieval.entity.stat import Stat, MetricName, PerInstanceStats
from agieval.entity.plugin_param.step_param import BaseMetricsPluginParam
from agieval.plugin.metrics.base_metrics import BaseMetrics


@MetricsPlugin
class ModelEvalSimpleqaMetrics(BaseMetrics[BaseMetricsPluginParam]):
    """
    SimpleQA scoring metric calculation
    """

    @classmethod
    def get_metrics_name(cls) -> str:
        """
        return metrics_name
        """
        return "model_eval_score_metrics"


    def run(self, scenario_state: ScenarioState, aggregate_stats: List[Stat], per_instance_stats: List[PerInstanceStats]) -> Tuple[Stat, Dict[str, Stat]]:
        # Used to store current metric results, which will be merged into per_instance_stats later
        per_instance_stats_local = dict()
        per_instance_stats_refuse = dict()

        aggregate_stat_local = Stat(MetricName(self.context_param.metrics_name))
        aggregate_stat_refuse = Stat(MetricName('model_eval_score_refuse'))

        for request_state in scenario_state.request_states:
            if request_state.model_score_result is None:
                self.log_error(f"model eval result missing, id: {request_state.instance.id}")
                raise Exception("model eval result missing")
            model_eval_score = self.model_eval_score(request_state)

            # Accuracy
            stat = Stat(MetricName(self.context_param.metrics_name)).add(model_eval_score['is_correct'])
            per_instance_stats_local[request_state.instance.id] = stat
            aggregate_stat_local.merge(stat)
            # Refusal rate
            stat = Stat(MetricName('model_eval_score_refuse')).add(model_eval_score['is_not_attempted'])
            per_instance_stats_refuse[request_state.instance.id] = stat
            aggregate_stat_refuse.merge(stat)


        # todo future: F1 , requires platform or algorithm support, this is internal to a subset, cannot get dataset aggregation status dataset
        return aggregate_stat_local, per_instance_stats_local

    def model_eval_score(self, request_state: RequestState):
        try:
            match = re.search(r"(A|B|C)", request_state.model_score_result)
            grade_letter = match.group(0) if match else "C"  # Default to "NOT_ATTEMPTED" if no match
            # Metrics based on grading response
            is_correct = 1 if grade_letter == "A" else 0
            is_incorrect = 1 if grade_letter == "B" else 0
            is_not_attempted = 1 if grade_letter == "C" else 0
            is_except = 0
        except:
            is_except = 1
            is_correct = 0
            is_incorrect = 0
            is_not_attempted = 0
        return {
            'is_correct': is_correct,
            'is_incorrect': is_incorrect,
            'is_not_attempted': is_not_attempted,
            'is_except': is_except
        }

