from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="NEXUS_", extra="ignore")

    app_name: str = "Nexus Babel Alexandria MVP"
    environment: Literal["dev", "test", "prod"] = "dev"
    database_url: str = "sqlite:///./nexus_babel.db"
    neo4j_uri: str | None = None
    neo4j_username: str | None = None
    neo4j_password: str | None = None
    corpus_root: Path = Field(default_factory=lambda: Path.cwd())
    object_storage_root: Path = Field(default_factory=lambda: Path.cwd() / "object_storage")
    public_blocked_terms: list[str] = Field(
        default_factory=lambda: [
            "kill",
            "self-harm",
            "hate",
            "ethnic cleansing",
            "bioweapon",
            "how to make a bomb",
        ]
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
