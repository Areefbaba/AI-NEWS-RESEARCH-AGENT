"""Application configuration management using Pydantic Settings."""

import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core settings and environment configuration."""

    # Application details
    APP_NAME: str = "AI News & Research Agent"
    APP_VERSION: str = "1.1.0"
    ENV: str = "development"
    DEBUG: bool = False

    # Storage and Cache
    DATABASE_PATH: str = os.path.join("data", "news_agent.db")
    CACHE_TTL_HOURS: int = 6
    DEFAULT_TIME_WINDOW_HOURS: int = 48

    # Multi-Model LLM Providers & Fallback Chain
    LLM_FALLBACK_ORDER: str = "groq,gemini,openai,ollama,heuristic"
    SUMMARY_TARGET_WORD_COUNT: int = 200

    # Groq API settings
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Google Gemini API settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # OpenAI API settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Local Ollama / Qwen LLM settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    OLLAMA_TIMEOUT_SECONDS: float = 30.0

    # Optional Search settings
    SEARCH_PROVIDER: str = "none"  # "none", "tavily", "serpapi"
    SEARCH_API_KEY: Optional[str] = None

    # HTTP Client Configuration
    REQUEST_TIMEOUT_SECONDS: float = 12.0
    MAX_RETRIES: int = 2
    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 (AINewsResearchAgent/1.0)"
    )

    # Ranking Weights
    WEIGHT_RELEVANCE: float = 0.25
    WEIGHT_IMPACT: float = 0.30
    WEIGHT_RECENCY: float = 0.20
    WEIGHT_SOURCE_QUALITY: float = 0.15
    WEIGHT_CORROBORATION: float = 0.10

    # Category constraints
    MAX_STORIES_PER_CATEGORY: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
