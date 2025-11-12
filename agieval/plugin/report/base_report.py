from abc import abstractmethod
from typing import TypeVar

from agieval.core.plugin.base_plugin import BaseStep
from agieval.core.plugin.plugins_decorator import ReportPlugin
from agieval.entity.scenario_state import ScenarioState
from agieval.entity.plugin_param.step_param import BaseReportPluginParam
from agieval.visualization.reportor import start_reportor

T = TypeVar('T', bound=BaseReportPluginParam)
class BaseReport(BaseStep[T]):

    @abstractmethod
    def run(self, scenario_state: ScenarioState, per_instance_stats, stats, **kwargs) -> None:
        pass


@ReportPlugin
class VisualizationReport(BaseReport[BaseReportPluginParam]):

    def run(self, scenario_state: ScenarioState, per_instance_stats, stats, **kwargs):
        self.log("===Visualization REPORT===")
        start_reportor(self.context_param.work_dir)