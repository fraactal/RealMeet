from functools import lru_cache
import json
from typing import Annotated
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


PLACEHOLDER_SECRETS = {"change-me-in-production", "secret", "changeme", "test"}
STRICT_ENVS = {"staging", "production", "prod"}


class Settings(BaseSettings):
    app_name: str = Field(default="RealMeet API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
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
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    smtp_timeout_seconds: int = Field(default=10, alias="SMTP_TIMEOUT_SECONDS")
    email_mode: str = Field(default="log", alias="EMAIL_MODE")
    default_meeting_provider: str = Field(default="mock", alias="DEFAULT_MEETING_PROVIDER")
    mock_meeting_base_url: str = Field(default="http://localhost:15173/mock-meeting", alias="MOCK_MEETING_BASE_URL")
    enable_docs: bool | None = Field(default=None, alias="ENABLE_DOCS")
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")
    rate_limit_max_requests: int = Field(default=10, alias="RATE_LIMIT_MAX_REQUESTS")
    enable_demo_seed: bool | None = Field(default=None, alias="ENABLE_DEMO_SEED")
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    google_oauth_client_id: str | None = Field(default=None, alias="GOOGLE_OAUTH_CLIENT_ID")
    google_oauth_client_secret: str | None = Field(default=None, alias="GOOGLE_OAUTH_CLIENT_SECRET")
    google_oauth_redirect_uri: str | None = Field(default=None, alias="GOOGLE_OAUTH_REDIRECT_URI")
    google_oauth_scopes: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["https://www.googleapis.com/auth/calendar.events"],
        alias="GOOGLE_OAUTH_SCOPES",
    )
    google_oauth_state_ttl_seconds: int = Field(default=600, alias="GOOGLE_OAUTH_STATE_TTL_SECONDS")
    google_token_encryption_key: str | None = Field(default=None, alias="GOOGLE_TOKEN_ENCRYPTION_KEY")
    whatsapp_cloud_enabled: bool = Field(default=False, alias="WHATSAPP_CLOUD_ENABLED")
    whatsapp_graph_api_version: str | None = Field(default=None, alias="WHATSAPP_GRAPH_API_VERSION")
    whatsapp_access_token: str | None = Field(default=None, alias="WHATSAPP_ACCESS_TOKEN")
    whatsapp_app_secret: str | None = Field(default=None, alias="WHATSAPP_APP_SECRET")
    whatsapp_webhook_verify_token: str | None = Field(default=None, alias="WHATSAPP_WEBHOOK_VERIFY_TOKEN")
    whatsapp_default_language: str = Field(default="es_CL", alias="WHATSAPP_DEFAULT_LANGUAGE")
    whatsapp_default_country_code: str | None = Field(default="CL", alias="WHATSAPP_DEFAULT_COUNTRY_CODE")
    whatsapp_phone_hmac_key: str | None = Field(default=None, alias="WHATSAPP_PHONE_HMAC_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("app_env")
    @classmethod
    def normalize_app_env(cls, value: str) -> str:
        normalized = value.lower().strip()
        allowed = {"development", "docker", "staging", "production", "prod", "test"}
        if normalized not in allowed:
            raise ValueError(f"APP_ENV must be one of: {', '.join(sorted(allowed))}")
        return normalized

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

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        for origin in value:
            stripped = origin.strip().rstrip("/")
            if stripped == "*":
                raise ValueError("CORS_ORIGINS cannot include wildcard when credentials are enabled")
            parsed = urlparse(stripped)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("CORS_ORIGINS entries must be explicit http(s) origins")
            normalized.append(stripped)
        return normalized

    @field_validator("default_meeting_provider")
    @classmethod
    def validate_meeting_provider(cls, value: str) -> str:
        allowed = {"mock", "google_meet", "zoom"}
        if value not in allowed:
            raise ValueError(f"DEFAULT_MEETING_PROVIDER must be one of: {', '.join(sorted(allowed))}")
        return value

    @field_validator("email_mode")
    @classmethod
    def validate_email_mode(cls, value: str) -> str:
        allowed = {"log", "smtp"}
        normalized = value.lower().strip()
        if normalized not in allowed:
            raise ValueError(f"EMAIL_MODE must be one of: {', '.join(sorted(allowed))}")
        return normalized

    @field_validator("rate_limit_window_seconds", "rate_limit_max_requests")
    @classmethod
    def validate_positive_int(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Rate limit values must be positive")
        return value

    @field_validator("google_oauth_scopes", mode="before")
    @classmethod
    def parse_google_oauth_scopes(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return ["https://www.googleapis.com/auth/calendar.events"]
            if stripped.startswith("["):
                parsed = json.loads(stripped)
                if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
                    raise ValueError("GOOGLE_OAUTH_SCOPES JSON must be an array of strings")
                return [item.strip() for item in parsed if item.strip()]
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value

    @field_validator("google_oauth_scopes")
    @classmethod
    def validate_google_oauth_scopes(cls, value: list[str]) -> list[str]:
        allowed = {"https://www.googleapis.com/auth/calendar.events"}
        if not value:
            return ["https://www.googleapis.com/auth/calendar.events"]
        invalid = sorted(set(value) - allowed)
        if invalid:
            raise ValueError(f"Unsupported GOOGLE_OAUTH_SCOPES entries: {', '.join(invalid)}")
        return value

    @field_validator("google_oauth_state_ttl_seconds")
    @classmethod
    def validate_google_state_ttl(cls, value: int) -> int:
        if value < 60 or value > 3600:
            raise ValueError("GOOGLE_OAUTH_STATE_TTL_SECONDS must be between 60 and 3600")
        return value

    @field_validator("whatsapp_default_country_code")
    @classmethod
    def validate_whatsapp_country_code(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip().upper()
        if len(normalized) != 2 or not normalized.isalpha():
            raise ValueError("WHATSAPP_DEFAULT_COUNTRY_CODE must be a two-letter ISO country code")
        return normalized

    @field_validator("whatsapp_default_language")
    @classmethod
    def validate_whatsapp_language(cls, value: str) -> str:
        normalized = value.strip().replace("-", "_")
        if len(normalized) < 2 or len(normalized) > 10:
            raise ValueError("WHATSAPP_DEFAULT_LANGUAGE is invalid")
        return normalized

    @field_validator("whatsapp_graph_api_version")
    @classmethod
    def validate_whatsapp_graph_version(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip()
        if not normalized.startswith("v") or "." not in normalized:
            raise ValueError("WHATSAPP_GRAPH_API_VERSION must use format vXX.X")
        return normalized

    @model_validator(mode="after")
    def validate_environment_safety(self) -> "Settings":
        if self.app_env in STRICT_ENVS:
            if self.secret_key.strip().lower() in PLACEHOLDER_SECRETS or len(self.secret_key.strip()) < 32:
                raise ValueError("SECRET_KEY must be non-placeholder and at least 32 characters in staging/production")
            if self.enable_demo_seed is True and self.app_env in {"production", "prod"}:
                raise ValueError("ENABLE_DEMO_SEED cannot be true in production")
            if self.debug:
                raise ValueError("DEBUG cannot be true in staging/production")
        return self

    @property
    def docs_enabled(self) -> bool:
        if self.enable_docs is not None:
            return self.enable_docs
        return self.app_env not in {"production", "prod"}

    @property
    def demo_seed_enabled(self) -> bool:
        if self.enable_demo_seed is not None:
            return self.enable_demo_seed
        return self.app_env in {"development", "docker", "test"}

    def critical_config_errors(self) -> list[str]:
        errors: list[str] = []
        if not self.secret_key.strip():
            errors.append("SECRET_KEY is required")
        if not self.database_url.strip():
            errors.append("DATABASE_URL is required")
        if not self.cors_origins:
            errors.append("CORS_ORIGINS must include at least one origin")
        if self.app_env in STRICT_ENVS and (
            self.secret_key.strip().lower() in PLACEHOLDER_SECRETS or len(self.secret_key.strip()) < 32
        ):
            errors.append("SECRET_KEY must be hardened for staging/production")
        if self.app_env in {"production", "prod"} and self.demo_seed_enabled:
            errors.append("ENABLE_DEMO_SEED must be false in production")
        return errors

    @property
    def google_oauth_configured(self) -> bool:
        return all(
            [
                self.google_oauth_client_id,
                self.google_oauth_client_secret,
                self.google_oauth_redirect_uri,
                self.google_token_encryption_key,
            ]
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
