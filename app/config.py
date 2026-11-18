"""Application settings, read from environment variables (.env)."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings. Fall back to local-dev defaults when unset."""

    secret_key: str
    database_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            secret_key=os.environ.get("SECRET_KEY", "dev-insecure-secret-key"),
            database_url=os.environ.get(
                "DATABASE_URL", "sqlite:////app/data/kanban.db"
            ),
        )


settings = Settings.from_env()
