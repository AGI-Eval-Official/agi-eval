from typing import TypeVar, List

from agieval.common.cache import Cache
from agieval.core.plugin.base_plugin import BaseStage
from agieval.core.plugin.plugins_decorator import ReportProcessorPlugin
from agieval.core.plugin.plugin_factory import PluginFactory
from agieval.entity.flow_config import PluginType
from agieval.plugin.report.base_report import BaseReport
from agieval.entity.plugin_param.stage_param import ReportProcessorPluginParam


T = TypeVar('T', bound=ReportProcessorPluginParam)
class ReportProcessor(BaseStage[T]):

    def cache_is_available(self) -> bool:
        return False

    @staticmethod
    def get_steps() -> List[PluginType]:
        return [PluginType.REPORT]

@ReportProcessorPlugin
class SimpleReportProcessor(ReportProcessor[ReportProcessorPluginParam]):

    def process(self):
        scenario_state = Cache.load_scenario_state(benchmark_id=self.context_param.benchmark_id)
        per_instance_stats = Cache.load_per_instance_stats(benchmark_id=self.context_param.benchmark_id)
        stats = Cache.load_stats(benchmark_id=self.context_param.benchmark_id)

        report_plugin = PluginFactory[BaseReport].get_plugin_by_type(PluginType.REPORT)
        report_plugin.run(scenario_state, per_instance_stats, stats)