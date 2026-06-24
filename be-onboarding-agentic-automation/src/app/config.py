from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = "openai"
    llm_model: str = "gpt-5.4-nano"
    llm_api_key: str = ""
    llm_base_url: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    kb_dir: Path = Path(__file__).parent.parent.parent / "kb"
    kb_upload_dir: Path | None = None
    kb_max_upload_mb: int = 10
    database_url: str = ""
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    rag_top_k: int = 5
    rag_candidates: int = 20
    rag_min_vector_score: float = 0.2
    rag_enable_answerability: bool = True

    @property
    def resolved_kb_upload_dir(self) -> Path:
        return self.kb_upload_dir or self.kb_dir / "_uploads"


settings = Settings()
