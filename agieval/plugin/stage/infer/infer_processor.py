import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TypeVar, List

from tqdm import tqdm

from agieval.common.cache import Cache
from agieval.core.plugin.base_plugin import BaseStage
from agieval.core.plugin.plugin_factory import PluginFactory
from agieval.core.plugin.plugins_decorator import InferProcessorPlugin
from agieval.entity.flow_config import PluginType
from agieval.entity.plugin_param.stage_param import InferProcessorPluginParam
from agieval.entity.scenario_state import ScenarioState
from agieval.plugin.agent.base_agent import BaseAgent
from agieval.plugin.model.base_model import BaseModel

T = TypeVar('T', bound=InferProcessorPluginParam)
class InferProcessor(BaseStage[T]):

    def cache_is_available(self) -> bool:
        scenario_state: ScenarioState = Cache.load_scenario_state(self.context_param.benchmark_id)
        first_result = scenario_state.request_states[0].result
        return first_result is not None and first_result.completions is not None

    @staticmethod
    def get_steps() -> List[PluginType]:
        return [PluginType.INFER_LOAD_MODEL, PluginType.INFER_AGENT]


class SimpleInferProcessorPluginParam(InferProcessorPluginParam):
    pass

@InferProcessorPlugin
class SimpleInferProcessor(InferProcessor[SimpleInferProcessorPluginParam]):

    def cache_is_available(self) -> bool:
        scenario_state: ScenarioState = Cache.load_scenario_state(self.context_param.benchmark_id)
        if scenario_state is None:
            return False
        for request_state in scenario_state.request_states:
            result = request_state.result
            if result is None or result.completions is None:
                return False
        return True

    def process(self):
        model = PluginFactory[BaseModel].get_plugin_by_type(PluginType.INFER_LOAD_MODEL)
        scenario_state: ScenarioState = Cache.load_scenario_state(self.context_param.benchmark_id)
            
        base_agent = PluginFactory[BaseAgent].get_plugin_by_type(PluginType.INFER_AGENT)
        concurrency = self.context_param.concurrency

        request_states = scenario_state.request_states
        if self.context_param.use_cache:
            request_states = [rs for rs in request_states if rs.result is None or rs.result.completions is None]
            self.log(f"Model inference stage using cache, total instance count: {len(scenario_state.request_states)}, cached count: {len(scenario_state.request_states) - len(request_states)}, pending processing count: {len(request_states)}")
            
        # Create index mapping for updating results in original order
        request_index_map = {id(request_state): idx for idx, request_state in enumerate(request_states)}
        completed_count = 0
        cache_update_interval = self.context_param.cache_update_interval  # Update cache every 10 completed tasks
        last_cache_update_time = time.time()
        cache_update_time_interval = self.context_param.cache_update_time_interval  # Force update cache every 30 seconds

        # Thread lock for protecting shared resources
        lock = threading.Lock()

        def process_single_request(request_state):
            return base_agent.run(model, request_state)

        def update_cache_if_needed(force=False):
            """Update cache based on conditions"""
            nonlocal last_cache_update_time
            current_time = time.time()

            if force or completed_count % cache_update_interval == 0 or \
               (current_time - last_cache_update_time) >= cache_update_time_interval:
                try:
                    Cache.save_scenario_state(scenario_state, self.context_param.benchmark_id)
                    last_cache_update_time = current_time
                    self.log(f"Cached {completed_count}/{len(request_states)} results")
                except Exception as e:
                    self.log(f"Cache update failed: {e}")

        # Use thread pool for concurrent execution
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            # Submit all tasks
            future_to_request = {
                executor.submit(process_single_request, request_state): request_state
                for request_state in request_states
            }

            # Use tqdm to display progress
            with tqdm(total=len(request_states), desc="Processing Instance") as pbar:
                for future in as_completed(future_to_request):
                    try:
                        result = future.result()
                        original_request = future_to_request[future]

                        # Thread-safely update results
                        with lock:
                            # Update result at original index
                            original_index = request_index_map[id(original_request)]
                            request_states[original_index] = result
                            completed_count += 1

                            # Check if cache needs to be updated
                            update_cache_if_needed()

                        pbar.update(1)
                    except Exception as e:
                        self.log(f"Error processing request: {e}")
                        with lock:
                            completed_count += 1
                        pbar.update(1)

        # Finally ensure all results are cached
        with lock:
            update_cache_if_needed(force=True)
        
        self.log(f"All {len(request_states)} tasks processed and cached")
