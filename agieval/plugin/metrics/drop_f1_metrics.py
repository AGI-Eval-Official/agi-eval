from pydantic import Field
from typing import List, Set, Tuple, Union, Dict
import json

from agieval.core.plugin.plugins_decorator import MetricsPlugin
from agieval.entity.scenario_state import ScenarioState
from agieval.entity.stat import Stat, MetricName, PerInstanceStats
from agieval.entity.plugin_param.step_param import BaseMetricsPluginParam
from agieval.plugin.metrics.base_metrics import BaseMetrics
from agieval.entity.reference import Reference

import re
import string
from scipy.optimize import linear_sum_assignment
import numpy as np

try:
    import jieba
except:
    pass

ANSWER_PATTERN = r"(?i)Answer\s*:\s*([^\n]+)"


def _tokenize(text: str) -> List[str]:
    return re.split(" |-", text)


def _lower(text: str) -> str:
    return text.lower()


def _is_number(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False


def _normalize_number(text: str) -> str:
    if _is_number(text):
        return str(float(text))
    else:
        return text


EXCLUDE = set(string.punctuation)


def _remove_punc(text: str) -> str:
    if not _is_number(text):
        return "".join(ch for ch in text if ch not in EXCLUDE)
    else:
        return text


def _remove_articles(text: str) -> str:
    regex = re.compile(r"\b(a|an|the)\b", re.UNICODE)
    return re.sub(regex, " ", text)


def _white_space_fix(text: str) -> str:
    return " ".join(text.split())


def _normalize_answer(text: str) -> str:
    """Lower text and remove punctuation, articles and extra whitespace."""

    parts = [
        _white_space_fix(_remove_articles(
            _normalize_number(_remove_punc(_lower(token)))))
        for token in _tokenize(text)
    ]
    parts = [part for part in parts if part.strip()]
    normalized = " ".join(parts).strip()
    return normalized


def _answer_to_bags(
        answer: Union[str, List[str], Tuple[str, ...]]
) -> Tuple[List[str], List[Set[str]]]:
    if isinstance(answer, (list, tuple)):
        raw_spans = answer
    else:
        raw_spans = [answer]
    normalized_spans: List[str] = []
    token_bags = []
    for raw_span in raw_spans:
        normalized_span = _normalize_answer(raw_span)
        normalized_spans.append(normalized_span)
        token_bags.append(set(normalized_span.split()))
    return normalized_spans, token_bags


def _match_numbers_if_present(gold_bag: Set[str], predicted_bag: Set[str]) -> bool:
    gold_numbers = set()
    predicted_numbers = set()
    for word in gold_bag:
        if _is_number(word):
            gold_numbers.add(word)
    for word in predicted_bag:
        if _is_number(word):
            predicted_numbers.add(word)
    if (not gold_numbers) or gold_numbers.intersection(predicted_numbers):
        return True
    return False


def _compute_f1(predicted_bag: Set[str], gold_bag: Set[str]) -> float:
    intersection = len(gold_bag.intersection(predicted_bag))
    if not predicted_bag:
        precision = 1.0
    else:
        precision = intersection / float(len(predicted_bag))
    if not gold_bag:
        recall = 1.0
    else:
        recall = intersection / float(len(gold_bag))
    f1 = (
             (2 * precision * recall) / (precision + recall)
             if not (precision == 0.0 and recall == 0.0)
             else 0.0
         ) * 100
    return f1


def _align_bags(predicted: List[Set[str]], gold: List[Set[str]]) -> List[float]:
    """
    Takes gold and predicted answer sets and first finds the optimal 1-1 alignment
    between them and gets maximum metric values over all the answers.
    """
    scores = np.zeros([len(gold), len(predicted)])
    for gold_index, gold_item in enumerate(gold):
        for pred_index, pred_item in enumerate(predicted):
            if _match_numbers_if_present(gold_item, pred_item):
                scores[gold_index, pred_index] = _compute_f1(
                    pred_item, gold_item)
    row_ind, col_ind = linear_sum_assignment(-scores)

    max_scores = np.zeros([max(len(gold), len(predicted))])
    for row, column in zip(row_ind, col_ind):
        max_scores[row] = max(max_scores[row], scores[row, column])
    return max_scores


def get_drop_metrics(
        predicted: Union[str, List[str], Tuple[str, ...]], gold: Union[str, List[str], Tuple[str, ...]]
) -> Tuple[float, float]:
    """
    Takes a predicted answer and a gold answer (that are both either a string or a list of
    strings), and returns exact match and the DROP F1 metric for the prediction.  If you are
    writing a script for evaluating objects in memory (say, the output of predictions during
    validation, or while training), this is the function you want to call, after using
    :func:`answer_json_to_strings` when reading the gold answer from the released data file.
    """
    predicted_bags = _answer_to_bags(predicted)
    gold_bags = _answer_to_bags(gold)

    if set(predicted_bags[0]) == set(gold_bags[0]) and len(predicted_bags[0]) == len(gold_bags[0]):
        exact_match = 1.0
    else:
        exact_match = 0.0

    f1_per_bag = _align_bags(predicted_bags[1], gold_bags[1])
    f1 = np.mean(f1_per_bag)
    f1 = round(f1, 2)
    return exact_match, f1


def drop_metric(sample: str, reference: list[str]) -> Tuple[float, float]:
    em_scores = []
    f1_scores = []
    for answer in reference:
        if answer.strip() != "":
            em, f1 = get_drop_metrics(sample, answer)
            em_scores.append(em)
            f1_scores.append(f1)
    return (max(em_scores), max(f1_scores))


@MetricsPlugin
class DropF1Metrics(BaseMetrics[BaseMetricsPluginParam]):
    """
    Basic prefix matching metric calculation
    """

    @classmethod
    def get_metrics_name(cls) -> str:
        """
        return metrics_name
        """
        return "drop_f1_metrics"

    def run(self, scenario_state: ScenarioState, aggregate_stats: List[Stat], per_instance_stats: List[PerInstanceStats]) -> Tuple[Stat, Dict[str, Stat]]:
        # Used to store current metric results, which will be merged into per_instance_stats later
        per_instance_stats_local = dict()
        aggregate_stat_local = Stat(MetricName(self.context_param.metrics_name))
        for request_state in scenario_state.request_states:
            # Get correct answers and model inference results
            golds: List[Reference] = [reference for reference in request_state.instance.references if
                                      reference.is_correct]
            pred: str = request_state.result.completions[0].text.strip()
            match = re.search(ANSWER_PATTERN, pred)
            extracted_answer = match.group(1) if match else pred

            em_score, f1_score = drop_metric(extracted_answer, [gold.output.text for gold in golds])

            # Calculate metrics
            # qpem_score = self.process_result([gold.output.text for gold in golds], pred)
            stat = Stat(MetricName(self.context_param.metrics_name)).add((f1_score/100))
            per_instance_stats_local[request_state.instance.id] = stat
            # Update aggregate_stat
            aggregate_stat_local.merge(stat)

        return aggregate_stat_local, per_instance_stats_local

    def process_result(self, targets: List[str], pred: str) -> float:
        if not pred:
            return 0
        pred = drop_postprocess(pred)
        if not pred:
            return 0
        for target in targets:
            if pred.strip() == target.strip():
                return 1
        return 0


def find_last_num(text: str):
    text = text.split(' ')[::-1]
    flag = False
    ret = ''
    for i in range(len(text)):
        s = text[i]
        for i in range(len(s)):
            if s[i].isdigit():
                flag = True
                ret = s
                break
        if flag:
            break
    ret1 = ''
    for i in range(len(ret)):
        # deal with potential float number
        if ret[i].isdigit() or ret[i] == '.':
            ret1 += ret[i]
    return ret1.strip('.')


def extract_last_name(text):
    # Use regular expressions to match the last consecutive words starting with uppercase letters, ignoring the first word of the string
    matches = re.findall(r'(?<!^)\b[A-Z][a-z]*\b(?:\s+\b[A-Z][a-z]*\b)*', text)
    if matches:
        # If matching words are found, return the last one
        return matches[-1]
    else:
        # If no matching words are found, return the last word (ignoring the first word)
        words = re.findall(r'\b\w+\b', text)
        return words[-1] if len(words) > 1 else None


def drop_postprocess(text: str) -> str:
    text = text.split('\n\n')[0]
    if 'answer is' in text:
        text = text.split('answer is')[1]
        text = text.split('.')[0]
        if re.search(r'\d', text):
            text = find_last_num(text)
    elif re.search(r'\d', text):
        text = find_last_num(text)
    else:
        # If there is no matching format and no numbers, take the uppercase entity.
        text = extract_last_name(text)
    return text
