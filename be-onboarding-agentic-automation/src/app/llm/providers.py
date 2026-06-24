import json
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import anthropic
from app.config import settings
from .base import Message


class ClaudeProvider:
    def __init__(self) -> None:
        api_key = settings.anthropic_api_key or settings.llm_api_key
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY or LLM_API_KEY is required for LLM_PROVIDER=claude")
        self._client = anthropic.Anthropic(api_key=api_key)

    def generate(self, system: str, messages: list[Message]) -> str:
        response = self._client.messages.create(
            model=settings.llm_model,
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=list(messages),
        )
        return response.content[0].text


class OpenAIProvider:
    """Provider for OpenAI's Responses API."""

    def __init__(self) -> None:
        self._api_key = settings.openai_api_key or settings.llm_api_key
        if not self._api_key:
            raise ValueError("OPENAI_API_KEY or LLM_API_KEY is required for LLM_PROVIDER=openai")

        base_url = settings.llm_base_url or "https://api.openai.com/v1"
        self._url = f"{base_url.rstrip('/')}/responses"

    def generate(self, system: str, messages: list[Message]) -> str:
        payload = {
            "model": settings.llm_model,
            "instructions": system,
            "input": [{"role": msg["role"], "content": msg["content"]} for msg in messages],
            "max_output_tokens": 1024,
        }
        data = _post_json(self._url, self._api_key, payload)

        output_text = data.get("output_text")
        if isinstance(output_text, str) and output_text:
            return output_text

        for item in data.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")
                if isinstance(text, str) and text:
                    return text

        raise ValueError("OpenAI response did not include text output")


class OpenAICompatibleProvider:
    """Provider for OpenAI-compatible Chat Completions APIs."""

    def __init__(self) -> None:
        self._api_key = settings.llm_api_key or settings.openai_api_key
        if not self._api_key:
            raise ValueError("LLM_API_KEY or OPENAI_API_KEY is required for LLM_PROVIDER=openai-compatible")

        base_url = settings.llm_base_url or "https://api.openai.com/v1"
        self._url = f"{base_url.rstrip('/')}/chat/completions"

    def generate(self, system: str, messages: list[Message]) -> str:
        payload = {
            "model": settings.llm_model,
            "messages": [{"role": "system", "content": system}, *messages],
            "max_tokens": 1024,
        }
        data = _post_json(self._url, self._api_key, payload)

        choices = data.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content")
            if isinstance(content, str) and content:
                return content

        raise ValueError("OpenAI-compatible response did not include message content")


class FakeProvider:
    """Echo provider for local testing without an API key."""

    def generate(self, system: str, messages: list[Message]) -> str:
        last = messages[-1]["content"] if messages else "(vacio)"
        return (
            "[FAKE] Echo de tu pregunta: "
            f'"{last}". '
            "Segun los documentos de onboarding, 30X es una escuela de negocios "
            "ejecutiva para founders, CEOs y altos directivos hispanohablantes. "
            "<source>01_organizacion.md - Que es 30X?</source>"
        )


def _post_json(url: str, api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"LLM API request failed with HTTP {exc.code}: {detail}") from exc
