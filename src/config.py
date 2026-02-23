"""Centralized environment configuration for Kelsen-Graph PoC.

This module defines a strict, validated contract for runtime settings and
provides a single cached settings instance for dependency injection.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime configuration loaded from environment and `.env`.

    Attributes:
        llm_api_key: API key used for authenticated LLM requests.
        llm_api_url: HTTP endpoint of the LLM provider.
        llm_mock_mode: Enables network-free mock mode for local/dev execution.
        llm_mock_response_json: Raw JSON response to use when mock mode is on.
        llm_model: LLM model identifier to request from the provider.
        llm_timeout_seconds: Network timeout for outbound provider requests.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    llm_api_key: str = Field(alias="LLM_API_KEY", min_length=1)
    llm_api_url: str | None = Field(default=None, alias="LLM_API_URL")
    llm_mock_mode: bool = Field(default=False, alias="LLM_MOCK_MODE")
    llm_mock_response_json: str | None = Field(
        default=None,
        alias="LLM_MOCK_RESPONSE_JSON",
    )
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL", min_length=1)
    llm_timeout_seconds: float = Field(default=30.0, alias="LLM_TIMEOUT_SECONDS", gt=0)

    @field_validator("llm_api_key")
    @classmethod
    def validate_non_blank_api_key(cls, value: str) -> str:
        """Reject blank API keys after stripping whitespace."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("LLM_API_KEY cannot be blank.")
        return normalized

    @model_validator(mode="after")
    def validate_runtime_mode(self) -> "Settings":
        """Enforce coherent settings for mock and real provider modes."""
        if self.llm_mock_mode and not self.llm_mock_response_json:
            raise ValueError(
                "LLM_MOCK_MODE is enabled but LLM_MOCK_RESPONSE_JSON is missing."
            )

        if not self.llm_mock_mode and not self.llm_api_url:
            raise ValueError(
                "LLM_API_URL is required when LLM_MOCK_MODE is disabled."
            )

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton-like settings instance."""
    return Settings()  # type: ignore[call-arg]
