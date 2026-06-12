"""
Settings — environment-based configuration using Pydantic Settings.

All configuration is sourced from environment variables or a .env file.
Secrets (API keys) are never hardcoded — they are read from the environment.

Usage:
    from config.settings import settings
    provider = ProviderFactory.create(settings.llm_provider, api_key=settings.llm_api_key)
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings backed by environment variables.

    Pydantic automatically reads from environment variables and .env files.
    The `model_config` controls the source priority and file location.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",         # Ignore unknown env vars
    )

    # ── LLM Provider ──────────────────────────────────────────────────────
    llm_provider: str = Field(
        default="gemini",
        description="LLM provider to use. One of: gemini, openai, claude, ollama.",
    )
    llm_api_key: str = Field(
        default="",
        description="API key for the selected LLM provider.",
    )
    llm_model: str = Field(
        default="gemini-flash-latest",
        description="Model variant to use (provider-specific).",
    )

    # ── Gemini Specific ───────────────────────────────────────────────────
    gemini_api_key: str | None = Field(
        default=None,
        description="Specific API key for Gemini. Falls back to llm_api_key if not set.",
    )
    gemini_model: str = Field(
        default="gemini-1.5-flash",
        description="Specific model for Gemini.",
    )
    gemini_timeout_seconds: int = Field(
        default=30,
        description="Timeout for Gemini API calls.",
    )
    gemini_max_retries: int = Field(
        default=3,
        description="Maximum number of retries for transient Gemini errors.",
    )

    # ── Embeddings ────────────────────────────────────────────────────────
    embedding_model: str = Field(
        default="models/text-embedding-004",
        description="Model variant to use for embeddings.",
    )
    embedding_batch_size: int = Field(
        default=100,
        ge=1,
        description="Maximum number of texts to embed in a single batch request.",
    )

    # ── Vector Store (Qdrant) ─────────────────────────────────────────────
    qdrant_url: str | None = Field(
        default=None,
        description="Qdrant Cloud URL. If set, overrides host/port.",
    )
    qdrant_api_key: str | None = Field(
        default=None,
        description="Qdrant Cloud API Key.",
    )
    qdrant_host: str = Field(
        default="localhost",
        description="Hostname for the Qdrant database.",
    )
    qdrant_port: int = Field(
        default=6333,
        description="Port for the Qdrant database.",
    )
    qdrant_collection: str = Field(
        default="knowledge_base",
        description="Name of the Qdrant collection.",
    )

    # ── Redis Cache & Queue ────────────────────────────────────────────────
    redis_url: str | None = Field(
        default=None,
        description="Full Redis connection URL (e.g., rediss://...). Overrides host/port.",
    )
    redis_host: str = Field(
        default="localhost",
        description="Hostname for the Redis database.",
    )
    redis_port: int = Field(
        default=6379,
        description="Port for the Redis database.",
    )
    redis_db: int = Field(
        default=0,
        description="DB index for the Redis database.",
    )

    # ── Agent tuning ──────────────────────────────────────────────────────
    agent_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="LLM temperature for extraction tasks. Low = more deterministic.",
    )
    agent_max_output_tokens: int = Field(
        default=4096,
        ge=256,
        description="Max tokens for LLM response.",
    )
    agent_min_resume_words: int = Field(
        default=30,
        ge=1,
        description="Minimum word count to accept a parsed document.",
    )

    # ── Logging ───────────────────────────────────────────────────────────
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR.",
    )
    log_format: str = Field(
        default="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        description="Python logging format string.",
    )


# Singleton settings instance — import this everywhere
settings = Settings()
