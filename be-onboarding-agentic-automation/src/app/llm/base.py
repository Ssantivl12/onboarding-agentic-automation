from typing import Literal, Protocol
from typing import TypedDict


class Message(TypedDict):
    role: Literal["user", "assistant"]
    content: str


class LLMProvider(Protocol):
    def generate(self, system: str, messages: list[Message]) -> str: ...
