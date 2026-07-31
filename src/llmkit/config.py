"""Central configuration. Secrets come from environment / .env — NEVER hardcoded.

Why this matters in production:
- API keys in code end up in git history forever (a real, common incident).
- pydantic-settings validates config at startup, so a missing key fails loudly
  at boot instead of mysteriously at request #3,000.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Providers — set whichever you use in .env
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""

    # Defaults you will tune per project
    default_model: str = "gemini-3.5-flash"  # cheap tier for iteration
    request_timeout_s: float = 60.0
    max_retries: int = 3

    # Observability
    log_level: str = "INFO"
    log_prompts: bool = True  # set False in environments where prompts may contain PII


@lru_cache
def get_settings() -> Settings:
    return Settings()
