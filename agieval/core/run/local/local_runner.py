

from agieval.common.logger import log
from agieval.core.run.runner import Runner
from agieval.core.run.local.local_dispatch_center import LocalDispatchCenter

class LocalRunner(Runner[LocalDispatchCenter]):

    def do_run(self):
        self.dispatch_center.dispatch_start()
        while self.dispatch_center.has_stage():
            self.dispatch_center.execute_stage(self, self.dispatch_center.current_benchmark, self.dispatch_center.current_stage, self.dispatch_center.eval_config)
            self.dispatch_center.next_stage()



