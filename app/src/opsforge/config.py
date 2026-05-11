from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPSFORGE_", env_file=".env", extra="ignore")

    app_name: str = "opsforge-local"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./opsforge.db"
    worker_poll_seconds: float = Field(default=2.0, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
