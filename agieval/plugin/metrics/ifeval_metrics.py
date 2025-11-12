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
class IFEvalMetrics(BaseMetrics[BaseMetricsPluginParam]):
    """
    IFEval
    """

    @classmethod
    def get_metrics_name(cls) -> str:
        """
        return metrics_name
        """
        return "quasi_prefix_exact_match"

    def run(self, scenario_state: ScenarioState, aggregate_stats: List[Stat], per_instance_stats: List[PerInstanceStats]) -> Tuple[Stat, Dict[str, Stat]]:
        
        per_instance_stats_local = dict()
        aggregate_stat_local = Stat(MetricName(self.context_param.metrics_name))
        for request_state in scenario_state.request_states:
            
            golds = [reference for reference in request_state.instance.references if reference.is_correct]
            pred: str = request_state.result.completions[0].text.strip()
            
            qpem_score = self.compute_score(pred, golds[0].output.text)
            stat = Stat(MetricName(self.context_param.metrics_name)).add(qpem_score)
            per_instance_stats_local[request_state.instance.id] = stat
            
            aggregate_stat_local.merge(stat)

        return aggregate_stat_local, per_instance_stats_local

    def compute_score(self, pred, gold):
        gold_count = gold.split('&|&')[0].split('_|_')
        gold_keyword = gold.split('&|&')[-1].split('_|_')
        f_score = 1
        for index, keyword in enumerate(gold_keyword):
            f_score *= float(self.count_match(gold_count[index], pred, keyword))
        return f_score

    def count_match(self, comparison_string: str, sentence: str, match: str) -> [int]:
        """
        Args:
            Text content to be matched and the answer
        Returns:
            Whether the count requirement is met
        """
        if match == "(w)":  # Questions with word count constraint
            count_key = len(re.findall(r'\b\w+\b', sentence))
        elif match == "(s)":  # Questions with sentence count constraint
            sentences = re.split(r'[.!?]', sentence)
            sentences = [sentence for sentence in sentences if sentence.strip()]
            count_key = len(sentences)
        elif match == "c":  # Questions with lowercase letter count constraint
            # Initialize counter
            lowercase_count = 0
            # Iterate through each character in the sentence and count lowercase and uppercase letters
            for char in sentence:
                if char.islower():
                    lowercase_count += 1
            count_key = lowercase_count
        elif match == "C":  # Questions with uppercase letter count constraint
            # Initialize counter
            uppercase_count = 0
            # Iterate through each character in the sentence and count lowercase and uppercase letters
            for char in sentence:
                if char.isupper():
                    uppercase_count += 1
            count_key = uppercase_count
        else:  # Questions with keyword count constraint
            # Use regular expressions to ensure only whole words are matched
            count_key = len(re.findall(re.escape(match), sentence))

        # Start matching judgment
        # Use regular expressions to extract operators and values
        if comparison_string == "-1":
            if match == "C":
                return int(sentence.isupper())
            elif match == "c":
                return int(sentence.islower())

        else:
            match = re.match(r'([<>=]=?)(\d+(?:\.\d+)?)', comparison_string)
            if match:
                operator = match.group(1)
                value = float(match.group(2))
                return self.compare(count_key, operator, value)

    def compare(self, num, op, val):
        if op == '<':
            return int(num < val)
        elif op == '<=':
            return int(num <= val)
        elif op == '>':
            return int(num > val)
        elif op == '>=':
            return int(num >= val)
        elif op == '=':
            return int(num == val)
        else:
            raise ValueError(f"Invalid operator: {op}")