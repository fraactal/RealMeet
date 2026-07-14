from app.core.config import Settings


def test_settings_accepts_json_cors() -> None:
    settings = Settings(
        SECRET_KEY="secret",
        DATABASE_URL="postgresql+pg8000://user:pass@localhost:25432/db",
        CORS_ORIGINS='["http://localhost:15173","http://127.0.0.1:15173"]',
    )
    assert settings.cors_origins == ["http://localhost:15173", "http://127.0.0.1:15173"]


def test_settings_accepts_csv_cors() -> None:
    settings = Settings(
        SECRET_KEY="secret",
        DATABASE_URL="postgresql+pg8000://user:pass@localhost:25432/db",
        CORS_ORIGINS="http://localhost:15173,http://127.0.0.1:15173",
    )
    assert settings.cors_origins == ["http://localhost:15173", "http://127.0.0.1:15173"]
