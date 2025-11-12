import re
import string

from pydantic import Field
from typing import List, Dict, Tuple

from agieval.core.plugin.plugins_decorator import MetricsPlugin
from agieval.entity.scenario_state import ScenarioState
from agieval.entity.stat import Stat, MetricName, PerInstanceStats
from agieval.entity.plugin_param.step_param import BaseMetricsPluginParam
from agieval.plugin.metrics.base_metrics import BaseMetrics
from agieval.entity.request_state import RequestState


@MetricsPlugin
class ModelEvalZeroshotV2Metrics(BaseMetrics[BaseMetricsPluginParam]):
    """
    Zeroshot Model Scoring Metrics Calculation
    """

    @classmethod
    def get_metrics_name(cls) -> str:
        """
        return metrics_name
        """
        return "model_eval_zeroshot_v2_metrics"

    def run(self, scenario_state: ScenarioState, aggregate_stats: List[Stat], per_instance_stats: List[PerInstanceStats]) -> Tuple[Stat, Dict[str, Stat]]:
        per_instance_stats_local = dict()
        aggregate_stat_local = Stat(MetricName(self.context_param.metrics_name))
        for request_state in scenario_state.request_states:
            if request_state.model_score_result is None:
                self.log_error(f"model eval result missing, id: {request_state.instance.id},benchmark_id:{self.context_param.benchmark_id},text:{request_state.instance.input.text}")
                raise Exception("model eval result missing")
            model_eval_score = self.model_eval_score(request_state)
            rule_based_score = self.rule_based_score(request_state)
            stat = Stat(MetricName(self.context_param.metrics_name)).add(max(model_eval_score, rule_based_score))
            per_instance_stats_local[request_state.instance.id] = stat
            # Update aggregate_stat
            aggregate_stat_local.merge(stat)

        return aggregate_stat_local, per_instance_stats_local


    def get_correct_result(self,  request_state: RequestState) -> Tuple[List[str], List[str], str]:
        correct_texts = []

        for reference in request_state.instance.references:
            if reference.is_correct:
                correct_text = reference.output.text
                correct_texts.append(correct_text)
        correct_keys = []
        if request_state.output_mapping:
            for key, value in request_state.output_mapping.items():
                for i in range(len(correct_texts)):
                    if value == correct_texts[i]:
                        correct_keys.append(key)
                        correct_texts[i] = key + ". " + correct_texts[i]
                        break

        correct_answer = correct_texts[0]
        return correct_texts, correct_keys, correct_answer

    def model_eval_score(self, request_state: RequestState) -> float:
        # Fix regular expression to correctly match scoring results
        pattern = r'"老师评分":\s*([^}]+)'
        match = re.search(pattern, request_state.model_score_result)
        model_eval_score = 0.0
        try:
            if match:
                raw_value = match.group(1).strip().strip('"')
                # Handle score format like "1/1"
                if '/' in raw_value:
                    parts = raw_value.split('/')
                    if len(parts) == 2:
                        numerator = float(parts[0].strip())
                        denominator = float(parts[1].strip())
                        if denominator != 0:
                            model_eval_score = numerator / denominator
                        else:
                            model_eval_score = 0.0
                else:
                    # Handle direct numeric format
                    model_eval_score = float(raw_value)

                # Ensure score is within reasonable range
                if model_eval_score < 0.0 or model_eval_score > 1.0:
                    model_eval_score = 0.0
            else:
                model_eval_score = 0.0
        except (ValueError, ZeroDivisionError):
            model_eval_score = 0.0

        self.log_debug(f"Instance {request_state.instance.id} model score: Raw={request_state.model_score_result}, Parsed={model_eval_score}")
        return model_eval_score

    def rule_based_score(self, request_state: RequestState) -> float:

        correct_texts, correct_keys,correct_answer = self.get_correct_result(request_state)
        origin_completion = request_state.result.completions[0].text.replace("<|endoftext|>", "\n")

        rule_base_score = 0.0
        for index, correct_text in enumerate(correct_texts):
            if self.normalize_text(origin_completion) == self.normalize_text(correct_text) or self.normalize_text(
                    origin_completion) == self.normalize_text(correct_answer):
                rule_base_score = 1.0
                break

            if len(correct_keys) > index:
                correct_text = correct_text.replace(correct_keys[index], "", 1)
                if self.normalize_text(origin_completion) == self.normalize_text(correct_text) or self.normalize_text(
                        origin_completion) == self.normalize_text(correct_answer) or self.normalize_text(
                    origin_completion).startswith(self.normalize_text(correct_answer)):
                    rule_base_score = 1.0
                    break
        if rule_base_score == 0.0:
            for correct_key in correct_keys:
                if len(self.normalize_text(correct_key)) > 0 and self.normalize_text(origin_completion) == self.normalize_text(
                        correct_key):
                    rule_base_score = 1.0
                    break
                if self.normalize_text(origin_completion).upper().startswith(correct_key):
                    # If the output matches the correct answer option prefix and the following character is not an option letter, the rule gives 1 point
                    if len(self.normalize_text(origin_completion)) > 1 and (
                            self.normalize_text(origin_completion)[1].upper() < 'A' or self.normalize_text(origin_completion)[1].upper() > 'Z') \
                            and self.normalize_text(origin_completion)[1] != ".":
                        rule_base_score = 1.0
                        break
        return rule_base_score

    def fetch_mapping(self, pred, output_mapping):
        if pred in output_mapping:
            return output_mapping.get(pred)
        for l in range(len(pred), 0, -1):
            if pred[:l] in output_mapping:
                return output_mapping.get(pred[:l])
        return pred