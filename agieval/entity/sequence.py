from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass(frozen=False)
class Token:
    """
    A `Token` represents one token position in a `Sequence`, which has the
    chosen `text` as well as the top probabilities under the model.

    Note: (text, logprob) could exist or not exist in `top_logprobs`.
    """

    # Text that was chosen
    text: str

    # Log probability of generating that
    logprob: float

    # text -> log probability of generating that
    top_logprobs: Dict[str, float]


@dataclass
class Sequence():
    """
    A text sequence, along with related token & logit information for that sequence.
    Generally represents a model's return information.
    """
    # The concatenation of all the tokens
    text: str

    # The sum of the log probabilities of all tokens
    logprob: float = 0.0

    # The tokens
    tokens: List[Token] = field(default_factory=list)

    input_token_num: Optional[int] = None

    output_token_num: Optional[int] = None

    # Why did the sequence finish?
    finish_reason: Optional[Dict] = None

    def __add__(self, other: "Sequence") -> "Sequence":
        return Sequence(self.text + other.text, self.logprob + other.logprob, self.tokens + other.tokens)
