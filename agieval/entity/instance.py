from dataclasses import dataclass
from typing import Optional, List, Any, Dict

from agieval.entity.reference import Reference

@dataclass()
class Input:
    """
    The input of an `Instance`.
    """
    text: str = None


@dataclass(frozen=True, eq=False)
class Instance:
    """
    An `Instance` represents one data point that we're evaluating on (e.g., one
    question in a QA task).
    """

    input: Input
    """The input"""

    references: List[Reference]
    """References that helps us evaluate"""

    split: Optional[str] = None
    """Split (e.g., train, valid, test)"""

    id: Optional[str] = None
    """Used to group Instances that were created from a particular Instance through data augmentation"""

    multi_turn_input: List[str] = None
    """Multi-turn dialogue input"""

    # URL for multimodal model input
    url: Optional[Any] = None

    extra_data: Optional[dict] = None


