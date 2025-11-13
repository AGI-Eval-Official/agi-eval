import time
from pydantic import Field
import litellm

from agieval.core.plugin.plugins_decorator import InferLoadModelPlugin
from agieval.entity.request import Request
from agieval.entity.request_result import RequestResult
from agieval.entity.sequence import Sequence
from agieval.plugin.model.base_model import BaseModel
from agieval.entity.plugin_param.step_param import BaseStepPluginParam


class ScoreLiteLLMModelPluginParam(BaseStepPluginParam):
    score_model: str = Field(default="", description="Scoring model name")
    score_base_url: str = Field(default="", description="Scoring model URL")
    score_api_key: str = Field(default="", description="Scoring model api_key")
    score_retry_time: int = Field(default=10, description="Scoring model retry count")
    score_retry_time_interval: int = Field(default=10, description="Scoring model retry interval time")
    score_custom_llm_provider: str = Field(default="openai", description="Scoring model custom llm_provider")


@InferLoadModelPlugin
class ScoreLiteLLMModel(BaseModel[ScoreLiteLLMModelPluginParam]):

    def run(self, request: Request) -> RequestResult:
        retry_count = 0
        while True:
            try:
                return self._run_once(request)
            except Exception as e:
                self.log_warn(
                    f"ScoreLiteLLMModel run error: {e}, retry {retry_count} / {self.context_param.score_retry_time}")
                retry_count += 1
                time.sleep(self.context_param.score_retry_time_interval)
                if retry_count >= self.context_param.score_retry_time:
                    self.log_error(
                        f"ScoreLiteLLMModel run error: {e}, failed after retry {self.context_param.score_retry_time} times")
                    raise e

    def _run_once(self, request: Request):
        response = litellm.completion(
            model=self.context_param.score_model,
            api_base=self.context_param.score_base_url,
            api_key=self.context_param.score_api_key,
            custom_llm_provider=self.context_param.score_custom_llm_provider,
            messages=request.messages_as_dict(),
            max_tokens=request.max_new_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            stop_sequences=request.stop_sequences

        )
        return RequestResult(
            completions=[Sequence(response.choices[0].message.content)]
        )