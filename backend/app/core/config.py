from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from PARKIT_-prefixed environment variables."""

    app_name: str = "Parkit API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./parkit.db"
    grid_cell_size_degrees: float = 0.0005

    model_config = SettingsConfigDict(env_prefix="PARKIT_", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
