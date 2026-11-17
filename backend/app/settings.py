from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "InsureTutor"
    model_base_url: str = "https://api.openai.com/v1"
    model_api_key: str = ""
    model_name: str = "gpt-4.1-mini"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_cache_path: Path = Path(".cache/fastembed")
    retrieval_top_k: int = 6
    corpus_path: Path = Path("data/corpus.json")
    static_path: Path = Path("frontend/dist")
    max_message_chars: int = 2_000
    max_history_messages: int = 12


@lru_cache
def get_settings() -> Settings:
    return Settings()

