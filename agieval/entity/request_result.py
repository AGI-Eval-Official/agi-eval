from dataclasses import dataclass, field

from typing import List, Optional

from agieval.entity.sequence import Sequence


@dataclass
class RequestResult():

    completions: Optional[List[Sequence]] = None

    thought: Optional[str] = None

    finish: bool = False

    error: Exception = None
