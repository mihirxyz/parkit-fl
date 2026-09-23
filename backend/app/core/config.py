from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_DB_FILE = Path(__file__).resolve().parent.parent / "db" / "parkit.db"


class Settings(BaseSettings):
    """Runtime settings loaded from PARKIT_-prefixed environment variables."""

    app_name: str = "Parkit API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = f"sqlite:///{_DB_FILE.as_posix()}"
    grid_cell_size_degrees: float = 0.0005
    grid_n: int = 3

    model_config = SettingsConfigDict(env_prefix="PARKIT_", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
