from pydantic import Field
from typing import List, Dict, Tuple
import json

from agieval.core.plugin.plugins_decorator import MetricsPlugin
from agieval.entity.scenario_state import ScenarioState
from agieval.entity.stat import Stat, MetricName, PerInstanceStats
from agieval.entity.plugin_param.step_param import BaseMetricsPluginParam
from agieval.plugin.metrics.base_metrics import BaseMetrics
from agieval.entity.reference import Reference

from agieval.plugin.metrics.instruction_follow.evaluation_main import InputExamples, test_instruction_following_strict


@MetricsPlugin
class MIFEvalMetrics(BaseMetrics[BaseMetricsPluginParam]):
    """
    MIFEval Instruction Following Metrics
    Based on Google Research's IFEval evaluation framework
    """

    @classmethod
    def get_metrics_name(cls) -> str:
        """
        return metrics_name
        """
        return "mifeval_metrics"

    def run(self, scenario_state: ScenarioState, aggregate_stats: List[Stat], per_instance_stats: List[PerInstanceStats]) -> Tuple[Stat, Dict[str, Stat]]:

        # Used to store current metric results, which will be merged into per_instance_stats later
        per_instance_stats_local = dict()
        aggregate_stat_local = Stat(
            MetricName(self.context_param.metrics_name))
        for request_state in scenario_state.request_states:
            # Get correct answers and model inference results
            golds: List[Reference] = [
                reference for reference in request_state.instance.references if reference.is_correct]
            pred: str = request_state.result.completions[0].text.strip()
            target = golds[0].output.text
            # Parse JSON string or dictionary
            if isinstance(target, str):
                # If it's a string, try to parse it as JSON
                try:
                    data = json.loads(target)
                except json.JSONDecodeError:
                    # If JSON parsing fails, try using ast.literal_eval (to handle single quotes)
                    import ast
                    data = ast.literal_eval(target)
            else:
                # If it's already a dictionary, use it directly
                data = target
            # Extract kwargs and remove None values
            cleaned_kwargs = []
            for kwarg in data['kwargs']:
                cleaned_kwarg = {k: v for k,
                                 v in kwarg.items() if v is not None}
                cleaned_kwargs.append(cleaned_kwarg)
            # Update kwargs in data
            data['kwargs'] = cleaned_kwargs
            # Extract required fields
            key = data['key']
            instruction_id_list = data['instruction_id_list']
            kwargs = data['kwargs']
            inputs = []
            inputs.append(
                InputExamples(key=key,
                              instruction_id_list=instruction_id_list,
                              kwargs=kwargs))
            prompt_to_response = {}
            prompt_to_response[key] = pred
            # get instruction following results
            for func, output_file_name in [
                (test_instruction_following_strict, "eval_results_strict"),
                # (test_instruction_following_loose, "eval_results_loose"),
            ]:
                outputs = []
                for inp in inputs:
                    outputs.append(func(inp, prompt_to_response))
                follow_all_instructions = [
                    o.follow_all_instructions for o in outputs]
                accuracy = sum(follow_all_instructions) / len(outputs)
            # Calculate metrics
            if follow_all_instructions[0] == True:
                qpem_score = 1.0
            else:
                qpem_score = 0.0
            # qpem_score = self.compute_score(pred,golds[0].output.text)
            stat = Stat(MetricName(self.context_param.metrics_name)
                        ).add(qpem_score)
            per_instance_stats_local[request_state.instance.id] = stat
            # Update aggregate_stat
            aggregate_stat_local.merge(stat)

        return aggregate_stat_local, per_instance_stats_local
