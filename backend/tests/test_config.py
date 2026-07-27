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
        LOG_LEVEL="warning",
        RATE_LIMIT_ENABLED=True,
    )
    assert settings.docs_enabled is False
    assert settings.demo_seed_enabled is False
    assert settings.cors_origins == ["https://staging.realmeet.example"]
    assert settings.log_level == "WARNING"


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
        ENABLE_DOCS=False,
        ENABLE_DEMO_SEED=False,
        RATE_LIMIT_ENABLED=True,
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


def test_staging_rejects_docs_or_demo_seed_enabled() -> None:
    base = {
        "APP_ENV": "staging",
        "SECRET_KEY": "staging-secret-with-at-least-32-chars",
        "DATABASE_URL": "postgresql+pg8000://user:pass@localhost:25432/db",
        "CORS_ORIGINS": "https://staging.realmeet.example",
    }
    with pytest.raises(ValidationError):
        Settings(**base, ENABLE_DOCS=True, ENABLE_DEMO_SEED=False)
    with pytest.raises(ValidationError):
        Settings(**base, ENABLE_DOCS=False, ENABLE_DEMO_SEED=True)


def test_staging_rejects_localhost_cors_unless_explicitly_allowed() -> None:
    base = {
        "APP_ENV": "staging",
        "SECRET_KEY": "staging-secret-with-at-least-32-chars",
        "DATABASE_URL": "postgresql+pg8000://user:pass@localhost:25432/db",
        "CORS_ORIGINS": "http://localhost:15173",
        "ENABLE_DOCS": False,
        "ENABLE_DEMO_SEED": False,
    }
    with pytest.raises(ValidationError):
        Settings(**base)

    settings = Settings(**base, STAGING_ALLOW_LOCALHOST=True, RATE_LIMIT_ENABLED=True)
    assert settings.staging_allow_localhost is True


def test_smtp_mode_requires_host() -> None:
    with pytest.raises(ValidationError):
        Settings(
            SECRET_KEY="secret",
            DATABASE_URL="postgresql+pg8000://user:pass@localhost:25432/db",
            CORS_ORIGINS="http://localhost:15173",
            EMAIL_MODE="smtp",
            SMTP_HOST="",
        )


def test_google_oauth_must_be_complete_when_configured() -> None:
    with pytest.raises(ValidationError):
        Settings(
            SECRET_KEY="secret",
            DATABASE_URL="postgresql+pg8000://user:pass@localhost:25432/db",
            CORS_ORIGINS="http://localhost:15173",
            GOOGLE_OAUTH_CLIENT_ID="client-id",
        )


def test_google_oauth_empty_values_are_disabled() -> None:
    settings = Settings(
        SECRET_KEY="secret",
        DATABASE_URL="postgresql+pg8000://user:pass@localhost:25432/db",
        CORS_ORIGINS="http://localhost:15173",
        GOOGLE_OAUTH_CLIENT_ID="",
        GOOGLE_OAUTH_CLIENT_SECRET="",
        GOOGLE_OAUTH_REDIRECT_URI="",
        GOOGLE_TOKEN_ENCRYPTION_KEY="",
    )

    assert settings.google_oauth_configured is False


def test_google_oauth_redirect_without_secrets_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(
            SECRET_KEY="secret",
            DATABASE_URL="postgresql+pg8000://user:pass@localhost:25432/db",
            CORS_ORIGINS="http://localhost:15173",
            GOOGLE_OAUTH_REDIRECT_URI="http://localhost:18000/api/v1/admin/integrations/oauth/google/callback",
        )


def test_google_oauth_complete_values_are_enabled() -> None:
    settings = Settings(
        SECRET_KEY="secret",
        DATABASE_URL="postgresql+pg8000://user:pass@localhost:25432/db",
        CORS_ORIGINS="http://localhost:15173",
        GOOGLE_OAUTH_CLIENT_ID="client-id",
        GOOGLE_OAUTH_CLIENT_SECRET="client-secret",
        GOOGLE_OAUTH_REDIRECT_URI="http://localhost:18000/api/v1/admin/integrations/oauth/google/callback",
        GOOGLE_TOKEN_ENCRYPTION_KEY="fernet-key-placeholder",
    )

    assert settings.google_oauth_configured is True

def test_whatsapp_enabled_requires_operational_secrets() -> None:
    with pytest.raises(ValidationError):
        Settings(
            SECRET_KEY="secret",
            DATABASE_URL="postgresql+pg8000://user:pass@localhost:25432/db",
            CORS_ORIGINS="http://localhost:15173",
            WHATSAPP_CLOUD_ENABLED=True,
            WHATSAPP_GRAPH_API_VERSION="v20.0",
        )


def test_access_token_expiration_has_safe_bounds() -> None:
    base = {
        "SECRET_KEY": "secret",
        "DATABASE_URL": "postgresql+pg8000://user:pass@localhost:25432/db",
        "CORS_ORIGINS": "http://localhost:15173",
    }
    with pytest.raises(ValidationError):
        Settings(**base, ACCESS_TOKEN_EXPIRE_MINUTES=0)
    with pytest.raises(ValidationError):
        Settings(**base, ACCESS_TOKEN_EXPIRE_MINUTES=1441)


def test_staging_requires_rate_limiting_enabled() -> None:
    with pytest.raises(ValidationError):
        Settings(
            APP_ENV="staging",
            SECRET_KEY="staging-secret-with-at-least-32-chars",
            DATABASE_URL="postgresql+pg8000://user:pass@localhost:25432/db",
            CORS_ORIGINS="https://staging.realmeet.example",
            ENABLE_DOCS=False,
            ENABLE_DEMO_SEED=False,
            RATE_LIMIT_ENABLED=False,
        )
