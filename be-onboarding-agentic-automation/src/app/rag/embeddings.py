import json
from typing import Any, Protocol
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.config import settings


class Embedder(Protocol):
    def embed_query(self, text: str) -> list[float]: ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIEmbedder:
    def __init__(self) -> None:
        if settings.embedding_provider.lower().strip() != "openai":
            raise ValueError("Only EMBEDDING_PROVIDER=openai is currently supported.")

        self._api_key = settings.openai_api_key or settings.llm_api_key
        if not self._api_key:
            raise ValueError("OPENAI_API_KEY or LLM_API_KEY is required for embeddings.")

        base_url = settings.llm_base_url or "https://api.openai.com/v1"
        self._url = f"{base_url.rstrip('/')}/embeddings"

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        payload: dict[str, Any] = {
            "model": settings.embedding_model,
            "input": texts,
        }
        if settings.embedding_dimensions > 0:
            payload["dimensions"] = settings.embedding_dimensions

        data = _post_json(self._url, self._api_key, payload)
        rows = sorted(data.get("data", []), key=lambda row: row.get("index", 0))
        embeddings = [row.get("embedding") for row in rows]
        if len(embeddings) != len(texts) or not all(isinstance(item, list) for item in embeddings):
            raise ValueError("Embedding API response did not include all embeddings.")
        return embeddings


def get_embedder() -> Embedder:
    return OpenAIEmbedder()


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
        raise ValueError(f"Embedding API request failed with HTTP {exc.code}: {detail}") from exc
