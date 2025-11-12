import re
import string
from typing import List, Any

from agieval.core.plugin.plugins_decorator import MetricsPlugin
from agieval.entity.plugin_param.step_param import BaseMetricsPluginParam
from agieval.entity.stat import Stat, MetricName
from agieval.plugin.metrics.base_metrics import BaseMetrics


@MetricsPlugin
class MultipleChoiceJointMetrics(BaseMetrics[BaseMetricsPluginParam]):
    """
    Basic prefix matching metric calculation
    """

    @classmethod
    def get_metrics_name(cls) -> str:
        """
        return metrics_name
        """
        return "quasi_prefix_exact_match"

    def run(self, scenario_state, aggregate_stats, per_instance_stats, **kwargs):
        # Used to store current metric results, which will be merged into per_instance_stats later
        per_instance_stats_local = dict()
        aggregate_stat_local = Stat(MetricName(self.context_param.metrics_name))
        for request_state in scenario_state.request_states:
            # Get correct answers and model inference results
            target = request_state.request.target
            correct_option = \
            [x.output.text for i, x in enumerate(request_state.instance.references) if "correct" in x.tags][0]
            wrong_options = [x.output.text for i, x in enumerate(request_state.instance.references) if
                             "correct" not in x.tags]
            prediction = request_state.result.completions[0].text.strip()
            # Calculate metrics
            score = self.process_result(target, correct_option, wrong_options, prediction)
            stat = Stat(MetricName(self.context_param.metrics_name)).add(score)
            per_instance_stats_local[request_state.instance.id] = stat
            # Update aggregate_stat
            aggregate_stat_local.merge(stat)
        return aggregate_stat_local, per_instance_stats_local

    def process_result(self, target: str, correct_option: str, wrong_options: List, pred: str) -> float:
        if not pred or not target:
            return 0

        pred = re.sub("Option | Option|option | option|选项", "", pred)
        pred = " ".join([sentence for sentence in pred.split("\n") if sentence])
        pred = " ".join([sentence for sentence in pred.split(" ") if sentence])

        pred = self.extract_answer(pred)
        if not pred:
            return 0

        if self.normalize_text(pred).startswith(self.normalize_text(target)):
            return 1

        if self.normalize_text(pred).startswith(self.normalize_text(correct_option)):
            return 1

        if self.normalize_text(f"{target}. {correct_option}") in self.normalize_text(pred):
            for wrong_option in wrong_options:
                if f". {wrong_option}" in pred:
                    return 0
            return 1

        return 0

    def extract_answer(self, completion):
        for answer_pattern in self.answer_patterns():
            if re.search(answer_pattern, completion):
                text = re.search(answer_pattern, completion).group(1)
                return text
        return completion

    def answer_patterns(self):
        return [
            r"correct is: \(?([A-Z]+)\)?",
            r"correct is \(?([A-Z]+)\)?",
            r"correct: \(?([A-Z]+)\)?",
            r"\(?([A-Z]+)\)? is the correct",
            r"\(?([A-Z]+)\)? is correct",
            r"nswer to the question is: \(?([A-Z]+)\)?",
            r"nswer to the question is \(?([A-Z]+)\)?",
            r"nswer to the question: \(?([A-Z]+)\)?",
            r"nswer to your question is: \(?([A-Z]+)\)?",
            r"nswer to your question is \(?([A-Z]+)\)?",
            r"nswer to your question: \(?([A-Z]+)\)?",
            r"nswer is: \(?([A-Z]+)\)?",
            r"nswer is \(?([A-Z]+)\)?",
            r"nswer: \(?([A-Z]+)\)?",
            r"正确的是：\s?\(?([A-Z]+)\)?",
            r"正确的是\s?\(?([A-Z]+)\)?",
            r"正确是\s?\(?([A-Z]+)\)?",
            r"正确：\s?\(?([A-Z]+)\)?",
            r"\(?([A-Z]+)\)?\s?是正确",
            r"答案应该是\s?\(?([A-Z]+)\)?",
            r"答案是：\s?\(?([A-Z]+)\)?",
            r"答案是\s?\(?([A-Z]+)\)?",
            r"答案为\s?\(?([A-Z]+)\)?",
            r"答案选\s?\(?([A-Z]+)\)?",
            r"答案：\s?\(?([A-Z]+)\)?",
        ]
