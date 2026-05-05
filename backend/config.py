"""
NyayaSetu — Configuration
Supports Ollama (local), OpenAI, and Gemini as LLM providers.
"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # LLM provider
    llm_provider: str = "ollama"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"

    # Database
    database_url: str = "sqlite+aiosqlite:///./nyayasetu.db"

    # File storage
    upload_dir: str = "./uploads"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
