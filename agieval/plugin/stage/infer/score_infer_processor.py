import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TypeVar

from pydantic import Field
from tqdm import tqdm

from agieval.common.cache import Cache
from agieval.core.plugin.plugin_factory import PluginFactory
from agieval.core.plugin.plugins_decorator import InferProcessorPlugin
from agieval.entity.flow_config import PluginType
from agieval.entity.plugin_param.stage_param import InferProcessorPluginParam
from agieval.entity.scenario_state import ScenarioState
from agieval.plugin.agent.base_agent import BaseAgent
from agieval.plugin.model.base_model import BaseModel
from agieval.plugin.stage.infer.infer_processor import InferProcessor, SimpleInferProcessorPluginParam

T = TypeVar('T', bound=InferProcessorPluginParam)


class ScoreInferProcessorPluginParam(SimpleInferProcessorPluginParam):
    pass


@InferProcessorPlugin
class ScoreInferProcessor(InferProcessor[ScoreInferProcessorPluginParam]):
    """
    Scoring inference processor - used to automatically score model inference results

    This processor will:
    1. Check if evaluation model inference results already exist
    2. Score instances that have inference results but no scoring results
    3. Use scoring model (such as gpt-4) to score answers
    4. Store scoring results in request_state.model_score_result
    """

    def cache_is_available(self) -> bool:
        """
        Check if scoring cache is available

        Conditions for scoring cache availability:
        1. scenario_state exists
        2. All request_states have evaluation model inference results (result is not empty)
        3. All request_states have scoring results (model_score_result is not empty)

        Returns:
            bool: Whether cache is available
        """
        scenario_state: ScenarioState = Cache.load_scenario_state(self.context_param.benchmark_id)
        if scenario_state is None:
            return False

        for request_state in scenario_state.request_states:
            # Check if evaluation model inference results exist
            result = request_state.result
            if result is None or result.completions is None:
                self.log_debug(f"Instance {request_state.instance.id} missing evaluation model inference results")
                return False

            # Check if scoring results exist
            if request_state.model_score_result is None:
                self.log_debug(f"Instance {request_state.instance.id} missing scoring results")
                return False

        self.log_debug("Scoring cache for all instances is available")
        return True

    def process(self):
        """
        Execute scoring inference processing

        Process:
        1. Load scoring model
        2. Load scenario state (containing evaluation model inference results)
        3. Get scoring Agent
        4. Filter instances that need scoring (have inference results but no scoring results)
        5. Execute scoring concurrently
        6. Update cache periodically
        """
        # 1. Load scoring model - find scoring model by name
        model_list = PluginFactory[BaseModel].get_plugins_by_type(PluginType.INFER_LOAD_MODEL)
        self.log_debug(f"Available model plugins: {[m.__class__.__name__ for m in model_list]}")

        score_model = None
        # Look for ScoreLiteLLMModel or other scoring models
        for model in model_list:
            if 'Score' in model.__class__.__name__ or 'OpenaiHttpModel' in model.__class__.__name__:
                score_model = model
                self.log(f"Found scoring model: {score_model.__class__.__name__}")
                break

        if score_model is None:
            # If no dedicated scoring model is found, use default model but log warning
            score_model = PluginFactory[BaseModel].get_plugin_by_type(PluginType.INFER_LOAD_MODEL)
            self.log_warn(f"No dedicated scoring model found, using default model: {score_model.__class__.__name__}")

        # 2. Load scenario state
        scenario_state: ScenarioState = Cache.load_scenario_state(self.context_param.benchmark_id)
        if scenario_state is None:
            self.log_error("Unable to load scenario state, scoring inference stage cannot be executed")
            return

        # 3. Get scoring Agent - get all registered INFER_AGENT and find scoring Agent
        agent_list = PluginFactory[BaseAgent].get_plugins_by_type(PluginType.INFER_AGENT)
        score_agent = None

        # Look for ModelScoreZeroshotV3Agent or other scoring Agents
        for agent in agent_list:
            if hasattr(agent, 'run_one') and 'Score' in agent.__class__.__name__:
                score_agent = agent
                self.log(f"Found scoring Agent: {agent.__class__.__name__}")
                break

        if score_agent is None:
            # If no dedicated scoring Agent is found, use the first Agent but log warning
            score_agent = agent_list[0] if agent_list else PluginFactory[BaseAgent].get_plugin_by_type(
                PluginType.INFER_AGENT)
            self.log_warn(f"No dedicated scoring Agent found, using default Agent: {score_agent.__class__.__name__}")
        concurrency = self.context_param.concurrency

        # 4. Filter instances that need scoring
        request_states = scenario_state.request_states

        # First check which instances already have evaluation model inference results
        requests_with_inference = [rs for rs in request_states if
                                   rs.result is not None and rs.result.completions is not None]
        if len(requests_with_inference) == 0:
            self.log_error("No instances have evaluation model inference results, please execute evaluation model inference stage first")
            return

        # If cache is enabled, filter out instances that already have scoring results
        if self.context_param.use_cache:
            requests_to_score = [rs for rs in requests_with_inference if rs.model_score_result is None]
            self.log(f"Scoring inference stage using cache, total instance count: {len(scenario_state.request_states)}, "
                     f"instances with evaluation model inference results: {len(requests_with_inference)}, "
                     f"cached scoring count: {len(requests_with_inference) - len(requests_to_score)}, "
                     f"instances to be scored this time: {len(requests_to_score)}")
        else:
            requests_to_score = requests_with_inference
            self.log(f"Scoring inference stage not using cache, instances to be scored: {len(requests_to_score)}")

        if len(requests_to_score) == 0:
            self.log("All instances have completed scoring, skipping scoring inference stage")
            return

        # 5. Create index mapping for updating results in original order
        request_index_map = {id(request_state): idx for idx, request_state in enumerate(requests_to_score)}
        completed_count = 0
        cache_update_interval = self.context_param.cache_update_interval
        last_cache_update_time = time.time()
        cache_update_time_interval = self.context_param.cache_update_time_interval

        # Thread lock for protecting shared resources
        lock = threading.Lock()

        def process_single_score_request(request_state):
            """Process single scoring request"""
            # If it's a scoring Agent, use run_one method, otherwise use run method
            # if hasattr(score_agent, 'run_one'):
            #     return score_agent.run_one(model, request_state)
            # else:
            #     return score_agent.run(model, request_state)

            return score_agent.run_one(score_model, request_state)

        def update_cache_if_needed(force=False):
            """Update cache based on conditions"""
            nonlocal last_cache_update_time
            current_time = time.time()

            if force or completed_count % cache_update_interval == 0 or \
                    (current_time - last_cache_update_time) >= cache_update_time_interval:
                try:
                    Cache.save_scenario_state(scenario_state, self.context_param.benchmark_id)
                    last_cache_update_time = current_time
                    self.log(f"{self.context_param.benchmark_id} cached {completed_count}/{len(requests_to_score)} scoring results")
                except Exception as e:
                    self.log(f"Cache update failed: {e}")

        # 6. Use thread pool to execute scoring concurrently
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            # Submit all scoring tasks
            future_to_request = {
                executor.submit(process_single_score_request, request_state): request_state
                for request_state in requests_to_score
            }

            # Use tqdm to display progress
            with tqdm(total=len(requests_to_score), desc="Scoring Instance") as pbar:
                for future in as_completed(future_to_request):
                    try:
                        result = future.result()
                        original_request = future_to_request[future]

                        # Thread-safely update results
                        with lock:
                            # Update result at original index
                            original_index = request_index_map[id(original_request)]
                            requests_to_score[original_index] = result
                            completed_count += 1

                            # Check if cache needs to be updated
                            update_cache_if_needed()

                        pbar.update(1)
                    except Exception as e:
                        self.log_error(f"Error processing scoring request: {e}")
                        with lock:
                            completed_count += 1
                        pbar.update(1)

        # 7. Finally ensure all results are cached
        with lock:
            update_cache_if_needed(force=True)

        self.log(f"All {len(requests_to_score)} scoring tasks processed and cached")
