from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

from agieval.entity.instance import Instance
from agieval.entity.request import Request
from agieval.entity.request_result import RequestResult


@dataclass()
class RequestState:
    """
    A `RequestState` represents a single `Request` made on behalf of an `Instance`.
    It should have all the information that's needed later for a `Metric` to be
    able to understand the `Request` and its `RequestResult`.
    """

    instance: Instance
    """Which instance we're evaluating"""

    request: Request
    """The request that is actually made"""

    output_mapping: Optional[Dict[str, str]] = None
    """How to map the completion text back to a real output (e.g., for multiple choice, "B" => "the second choice")"""

    result: Optional[RequestResult] = None
    """The result of the request (filled in when the request is executed)"""

    model_score_request: Optional[Any] = None
    """actual prompt that send to the score model"""

    model_score_result: Optional[Any] = None
    """raw result of model score, might be a json object containing the score"""

    multi_turn_requests: List[Any] = field(default_factory=list, hash=False)
    """The requests of multi-turn conversation"""

    multi_turn_results: List[Any] = field(default_factory=list, hash=False)
    """The results of multi-turn conversation"""

    # Flag to indicate if this data comes from cache, True if cached
    cached: Any = None

    # Extra information
    extra_data: Optional[Any] = None