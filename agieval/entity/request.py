from dataclasses import dataclass, field, asdict
from typing import List


@dataclass
class Message():
    role: str
    content: str

    def to_dict(self):
        return asdict(self)

@dataclass
class Request():
    messages: List[Message] = field(default_factory=list)

    max_new_tokens: int = 4096
    
    temperature: float = 0.6

    top_k: int = -1

    top_p: float = 0.95

    frequency_penalty: float | None = None

    presence_penalty: float | None = None

    stop_sequences: List[str] = field(default_factory=list)

    def messages_as_dict(self):
        return [message.to_dict() for message in self.messages]
