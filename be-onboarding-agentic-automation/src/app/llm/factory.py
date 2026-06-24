from app.config import settings
from .base import LLMProvider
from .providers import ClaudeProvider, FakeProvider, OpenAICompatibleProvider, OpenAIProvider


def get_provider() -> LLMProvider:
    provider = settings.llm_provider.lower().strip()
    match provider:
        case "claude" | "anthropic":
            return ClaudeProvider()
        case "openai":
            return OpenAIProvider()
        case "openai-compatible":
            return OpenAICompatibleProvider()
        case "fake":
            return FakeProvider()
        case _:
            raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}")
