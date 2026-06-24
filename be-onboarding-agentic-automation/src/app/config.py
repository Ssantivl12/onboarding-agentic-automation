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


settings = Settings()
