from functools import lru_cache
import json
from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="RealMeet API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    secret_key: str = Field(..., alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=120, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    database_url: str = Field(..., alias="DATABASE_URL")
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:15173"],
        alias="CORS_ORIGINS",
    )
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(default="noreply@realmeet.local", alias="SMTP_FROM_EMAIL")
    smtp_from_name: str = Field(default="RealMeet", alias="SMTP_FROM_NAME")
    default_meeting_provider: str = Field(default="mock", alias="DEFAULT_MEETING_PROVIDER")
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                parsed = json.loads(stripped)
                if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
                    raise ValueError("CORS_ORIGINS JSON must be an array of strings")
                return [item.strip() for item in parsed if item.strip()]
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value

    @field_validator("default_meeting_provider")
    @classmethod
    def validate_meeting_provider(cls, value: str) -> str:
        allowed = {"mock", "google_meet", "zoom"}
        if value not in allowed:
            raise ValueError(f"DEFAULT_MEETING_PROVIDER must be one of: {', '.join(sorted(allowed))}")
        return value

    @model_validator(mode="after")
    def validate_production_safety(self) -> "Settings":
        if self.app_env.lower() in {"production", "prod"} and self.secret_key == "change-me-in-production":
            raise ValueError("SECRET_KEY must be changed in production")
        return self

    def critical_config_errors(self) -> list[str]:
        errors: list[str] = []
        if not self.secret_key.strip():
            errors.append("SECRET_KEY is required")
        if not self.database_url.strip():
            errors.append("DATABASE_URL is required")
        if not self.cors_origins:
            errors.append("CORS_ORIGINS must include at least one origin")
        return errors


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
