from typing import Any, TypeVar, List, Dict

from agieval.core.plugin.base_plugin import BaseStage
from agieval.core.plugin.plugins_decorator import MetricsProcessorPlugin
from agieval.core.plugin.plugin_factory import PluginFactory
from agieval.entity.flow_config import PluginType
from agieval.entity.plugin_param.stage_param import MetricsProcessorPluginParam
from agieval.plugin.metrics.base_metrics import BaseMetrics
from agieval.entity.stat import Stat, PerInstanceStats
from agieval.common.cache import Cache


T = TypeVar('T', bound=MetricsProcessorPluginParam)
class MetricsProcessor(BaseStage[T]):

    def cache_is_available(self) -> bool:
        stats: List[Stat] | None = Cache.load_stats(self.context_param.benchmark_id)
        return stats is not None and len(stats) > 0

    @staticmethod
    def get_steps() -> List[PluginType]:
        return [PluginType.METRICS]

@MetricsProcessorPlugin
class SimpleMetricsProcessor(MetricsProcessor[MetricsProcessorPluginParam]):

    def process(self):

        scenario_state = Cache.load_scenario_state(benchmark_id=self.context_param.benchmark_id)
       
        metrics_list: list[BaseMetrics] = [    
            PluginFactory[BaseMetrics].get_plugin_by_name(plugin_name=plugin.plugin_implement, runtime_param=plugin.context_params)
            for plugin in self.plugin_list
        ]
        
        aggregate_stats: List[Stat] = []
        per_instance_stats: List[PerInstanceStats] = []
        for metrics in metrics_list:
            aggregate_stat_local, per_instance_stats_local = metrics.run(scenario_state, aggregate_stats, per_instance_stats)
            # Merge current metric into common per_instance_stats:
            per_instance_stats = self.merge_per_instance_stat(per_instance_stats, per_instance_stats_local)
            # Update aggregate_stat:
            aggregate_stats = self.merge_aggregate_stats(aggregate_stats, aggregate_stat_local, stat_key=metrics.context_param.metrics_name)

    
        Cache.save_stats(aggregate_stats, self.context_param.benchmark_id)
        Cache.save_per_instance_stat(per_instance_stats, self.context_param.benchmark_id)
        Cache.save_scenario_state(scenario_state, self.context_param.benchmark_id)

    def merge_per_instance_stat(self, global_per_instance_stats: List[PerInstanceStats],
                                local_per_instance_stats: Dict[str, Stat]):
        """
        Merge the calculated per_instance_stats for this metric into global_per_instance_stats
        :param global_per_instance_stats:
        :param local_per_instance_stats:
        :return:
        """
        global_map: Dict[str, PerInstanceStats] = {x.instance_id: x for x in global_per_instance_stats}
        for instance_id, stat in local_per_instance_stats.items():
            if instance_id in global_map:
                exist = False
                for i in range(len(global_map[instance_id].stats)):
                    if global_map[instance_id].stats[i].name.name == stat.name.name:
                        global_map[instance_id].stats[i] = stat
                        exist = True
                        break
                if not exist:
                    global_map[instance_id].stats.append(stat)
            else:
                global_per_instance_stats.append(PerInstanceStats(instance_id, [stat]))
        return global_per_instance_stats

    def merge_aggregate_stats(self, global_aggregate_stats: List[Stat], local_aggregate_stats: Stat, stat_key=""):
        exist = False
        if stat_key is None:
            stat_key = ""
        for i in range(len(global_aggregate_stats)):
            if global_aggregate_stats[i].name.name == stat_key:
                global_aggregate_stats[i] = local_aggregate_stats
                exist = True
                break
        if not exist:
            global_aggregate_stats.append(local_aggregate_stats)
        return global_aggregate_stats

