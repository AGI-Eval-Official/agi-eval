from dataclasses import dataclass
from typing import List, Optional, Any

from agieval.common.constant import CORRECT_TAG


@dataclass(frozen=True)
class Output:
    """
    The output of a `Reference`.
    """

    text: str = None


@dataclass
class Reference:

    output: Output
    """The output"""

    tags: List[str]
    """Extra metadata (e.g., whether it's correct/factual/toxic)"""

    weight: Optional[float] = None
    """The weight value of the option, representing the probability or score of being correct"""

    extra: Optional[Any] = None
    
    @property
    def is_correct(self) -> bool:
        return CORRECT_TAG in self.tags
    
    @property
    def get_weight(self) -> float:
        return self.weight