from dataclasses import dataclass, field

from typing import List, Optional


@dataclass
class Prompt:
    """Result of prompt construction."""

    # Prompt prefix
    prompt_prefix: str = ''

    # Prompt suffix
    prompt_suffix: str = ''

    # Instance prefix, carried over from `AdapterSpec`
    instance_prefix: str = ''

    # Instructions for the task
    instructions_block: str = ''

    # Train instance blocks for the prompt
    train_instance_blocks: List[str] = field(default_factory=list)

    # Evaluation instance
    eval_instance_block: str = ''

    # If the prompt (instructions + test input) needs to be truncated to fit the model's context window,
    # this is the truncated text.
    truncated_text: Optional[str] = None

    @property
    def text(self) -> str:
        # Text for the prompt, might be truncated
        if self.truncated_text:
            return self.truncated_text

        # Construct non-truncated input
        blocks: List[str] = (
            ([self.instructions_block] if self.instructions_block else [])
            + self.train_instance_blocks
            + [self.eval_instance_block]
        )
        non_truncated_text: str = self.instance_prefix.join(blocks)

        # Note: this could be implemented via substitutions.
        if self.prompt_prefix:
            non_truncated_text = f"{self.prompt_prefix}{non_truncated_text}"
        if self.prompt_suffix:
            non_truncated_text = f"{non_truncated_text}{self.prompt_suffix}"
        return non_truncated_text

    @property
    def truncated(self) -> bool:
        return self.truncated_text is not None

    @property
    def num_train_instances(self) -> int:
        # Number of training instances in the prompt
        return len(self.train_instance_blocks)
