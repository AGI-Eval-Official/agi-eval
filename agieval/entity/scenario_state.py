from dataclasses import dataclass, field

from typing import List, Dict

from agieval.entity.request_state import RequestState


@dataclass
class ScenarioState:

    request_states: List[RequestState] = field(default=list)

    extra_configs: Dict = field(default_factory=dict)
