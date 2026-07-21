from functools import lru_cache
import json
from typing import Annotated
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


PLACEHOLDER_SECRETS = {"change-me-in-production", "secret", "changeme", "test"}
STRICT_ENVS = {"staging", "production", "prod"}
LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


class Settings(BaseSettings):
    app_name: str = Field(default="RealMeet API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
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
    staging_allow_localhost: bool = Field(default=False, alias="STAGING_ALLOW_LOCALHOST")
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
    whatsapp_webhook_public_url: str | None = Field(default=None, alias="WHATSAPP_WEBHOOK_PUBLIC_URL")
    whatsapp_webhook_max_body_bytes: int = Field(default=262144, alias="WHATSAPP_WEBHOOK_MAX_BODY_BYTES")
    whatsapp_webhook_event_retention_days: int = Field(default=30, alias="WHATSAPP_WEBHOOK_EVENT_RETENTION_DAYS")
    whatsapp_webhook_require_signature: bool = Field(default=True, alias="WHATSAPP_WEBHOOK_REQUIRE_SIGNATURE")
    whatsapp_http_connect_timeout_seconds: float = Field(default=3.0, alias="WHATSAPP_HTTP_CONNECT_TIMEOUT_SECONDS")
    whatsapp_http_read_timeout_seconds: float = Field(default=8.0, alias="WHATSAPP_HTTP_READ_TIMEOUT_SECONDS")
    whatsapp_http_total_timeout_seconds: float = Field(default=10.0, alias="WHATSAPP_HTTP_TOTAL_TIMEOUT_SECONDS")

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

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper().strip()
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        if normalized not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(sorted(allowed))}")
        return normalized

    @field_validator("access_token_expire_minutes")
    @classmethod
    def validate_access_token_expiration(cls, value: int) -> int:
        if value < 5 or value > 1440:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 5 and 1440")
        return value

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

    @field_validator("whatsapp_webhook_max_body_bytes")
    @classmethod
    def validate_whatsapp_webhook_size(cls, value: int) -> int:
        if value < 1024 or value > 1048576:
            raise ValueError("WHATSAPP_WEBHOOK_MAX_BODY_BYTES must be between 1024 and 1048576")
        return value

    @field_validator("whatsapp_webhook_event_retention_days")
    @classmethod
    def validate_whatsapp_retention(cls, value: int) -> int:
        if value < 1 or value > 365:
            raise ValueError("WHATSAPP_WEBHOOK_EVENT_RETENTION_DAYS must be between 1 and 365")
        return value

    @field_validator("whatsapp_http_connect_timeout_seconds", "whatsapp_http_read_timeout_seconds", "whatsapp_http_total_timeout_seconds")
    @classmethod
    def validate_whatsapp_timeout(cls, value: float) -> float:
        if value <= 0 or value > 60:
            raise ValueError("WhatsApp HTTP timeouts must be between 0 and 60 seconds")
        return value

    @model_validator(mode="after")
    def validate_environment_safety(self) -> "Settings":
        if self.app_env in STRICT_ENVS:
            if self.secret_key.strip().lower() in PLACEHOLDER_SECRETS or len(self.secret_key.strip()) < 32:
                raise ValueError("SECRET_KEY must be non-placeholder and at least 32 characters in staging/production")
            if self.docs_enabled:
                raise ValueError("ENABLE_DOCS must be false in staging/production")
            if self.demo_seed_enabled:
                raise ValueError("ENABLE_DEMO_SEED must be false in staging/production")
            if self.debug:
                raise ValueError("DEBUG cannot be true in staging/production")
            if not self.rate_limit_enabled:
                raise ValueError("RATE_LIMIT_ENABLED must be true in staging/production")
            local_origins = [origin for origin in self.cors_origins if _is_local_origin(origin)]
            if local_origins and not (self.app_env == "staging" and self.staging_allow_localhost):
                raise ValueError("CORS_ORIGINS cannot include localhost in staging/production")
            if self.whatsapp_cloud_enabled and not self.whatsapp_webhook_require_signature:
                raise ValueError("WHATSAPP_WEBHOOK_REQUIRE_SIGNATURE must be true when WhatsApp is enabled in staging/production")
        if self.email_mode == "smtp":
            if not self.smtp_host:
                raise ValueError("SMTP_HOST is required when EMAIL_MODE=smtp")
            if not self.smtp_from_email:
                raise ValueError("SMTP_FROM_EMAIL is required when EMAIL_MODE=smtp")
        google_values = [
            self.google_oauth_client_id,
            self.google_oauth_client_secret,
            self.google_oauth_redirect_uri,
            self.google_token_encryption_key,
        ]
        if any(google_values) and not all(google_values):
            raise ValueError("Google OAuth settings must be complete when any Google OAuth value is configured")
        if self.whatsapp_cloud_enabled:
            required_whatsapp = {
                "WHATSAPP_GRAPH_API_VERSION": self.whatsapp_graph_api_version,
                "WHATSAPP_ACCESS_TOKEN": self.whatsapp_access_token,
                "WHATSAPP_APP_SECRET": self.whatsapp_app_secret,
                "WHATSAPP_WEBHOOK_VERIFY_TOKEN": self.whatsapp_webhook_verify_token,
                "WHATSAPP_PHONE_HMAC_KEY": self.whatsapp_phone_hmac_key,
            }
            missing_whatsapp = [name for name, value in required_whatsapp.items() if not value]
            if missing_whatsapp:
                raise ValueError(f"Missing WhatsApp settings when enabled: {', '.join(missing_whatsapp)}")
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
        if self.app_env in STRICT_ENVS and self.docs_enabled:
            errors.append("ENABLE_DOCS must be false in staging/production")
        if self.app_env in STRICT_ENVS and self.demo_seed_enabled:
            errors.append("ENABLE_DEMO_SEED must be false in staging/production")
        if self.app_env in STRICT_ENVS and not self.rate_limit_enabled:
            errors.append("RATE_LIMIT_ENABLED must be true in staging/production")
        if self.app_env in STRICT_ENVS:
            local_origins = [origin for origin in self.cors_origins if _is_local_origin(origin)]
            if local_origins and not (self.app_env == "staging" and self.staging_allow_localhost):
                errors.append("CORS_ORIGINS cannot include localhost in staging/production")
        if self.email_mode == "smtp" and not self.smtp_host:
            errors.append("SMTP_HOST is required when EMAIL_MODE=smtp")
        if any(
            [
                self.google_oauth_client_id,
                self.google_oauth_client_secret,
                self.google_oauth_redirect_uri,
                self.google_token_encryption_key,
            ]
        ) and not self.google_oauth_configured:
            errors.append("Google OAuth settings must be complete when configured")
        if self.whatsapp_cloud_enabled:
            if not self.whatsapp_graph_api_version:
                errors.append("WHATSAPP_GRAPH_API_VERSION is required when WhatsApp is enabled")
            if not self.whatsapp_access_token:
                errors.append("WHATSAPP_ACCESS_TOKEN is required when WhatsApp is enabled")
            if not self.whatsapp_app_secret:
                errors.append("WHATSAPP_APP_SECRET is required when WhatsApp is enabled")
            if not self.whatsapp_webhook_verify_token:
                errors.append("WHATSAPP_WEBHOOK_VERIFY_TOKEN is required when WhatsApp is enabled")
            if not self.whatsapp_phone_hmac_key:
                errors.append("WHATSAPP_PHONE_HMAC_KEY is required when WhatsApp is enabled")
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


def _is_local_origin(origin: str) -> bool:
    parsed = urlparse(origin)
    return parsed.hostname in LOCAL_HOSTS


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
