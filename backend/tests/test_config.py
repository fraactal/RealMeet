import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_accepts_json_cors() -> None:
    settings = Settings(
        SECRET_KEY="secret",
        DATABASE_URL="postgresql+pg8000://user:pass@localhost:25432/db",
        CORS_ORIGINS='["http://localhost:15173","http://127.0.0.1:15173"]',
    )
    assert settings.cors_origins == ["http://localhost:15173", "http://127.0.0.1:15173"]


def test_settings_rejects_cors_wildcard_with_credentials() -> None:
    with pytest.raises(ValidationError):
        Settings(
            SECRET_KEY="secret",
            DATABASE_URL="postgresql+pg8000://user:pass@localhost:25432/db",
            CORS_ORIGINS="*",
        )


def test_staging_rejects_placeholder_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(
            APP_ENV="staging",
            SECRET_KEY="change-me-in-production",
            DATABASE_URL="postgresql+pg8000://user:pass@localhost:25432/db",
            CORS_ORIGINS="https://staging.realmeet.example",
        )


def test_staging_accepts_hardened_secret_and_explicit_cors() -> None:
    settings = Settings(
        APP_ENV="staging",
        SECRET_KEY="staging-secret-with-at-least-32-chars",
        DATABASE_URL="postgresql+pg8000://user:pass@localhost:25432/db",
        CORS_ORIGINS="https://staging.realmeet.example",
        ENABLE_DOCS=False,
        ENABLE_DEMO_SEED=False,
    )
    assert settings.docs_enabled is False
    assert settings.demo_seed_enabled is False
    assert settings.cors_origins == ["https://staging.realmeet.example"]


def test_demo_seed_defaults_to_local_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENABLE_DEMO_SEED", raising=False)
    development = Settings(
        APP_ENV="development",
        SECRET_KEY="secret",
        DATABASE_URL="postgresql+pg8000://user:pass@localhost:25432/db",
        CORS_ORIGINS="http://localhost:15173",
    )
    staging = Settings(
        APP_ENV="staging",
        SECRET_KEY="staging-secret-with-at-least-32-chars",
        DATABASE_URL="postgresql+pg8000://user:pass@localhost:25432/db",
        CORS_ORIGINS="https://staging.realmeet.example",
    )
    assert development.demo_seed_enabled is True
    assert staging.demo_seed_enabled is False


def test_settings_accepts_csv_cors() -> None:
    settings = Settings(
        SECRET_KEY="secret",
        DATABASE_URL="postgresql+pg8000://user:pass@localhost:25432/db",
        CORS_ORIGINS="http://localhost:15173,http://127.0.0.1:15173",
    )
    assert settings.cors_origins == ["http://localhost:15173", "http://127.0.0.1:15173"]
