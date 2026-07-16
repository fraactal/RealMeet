from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.integrations.google_workspace.enums import GoogleWorkspaceHealthStatus, GoogleWorkspaceServiceKey


class GoogleWorkspaceSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    calendar_enabled: bool | None = None
    meet_enabled: bool | None = None
    sheets_enabled: bool | None = None
    drive_enabled: bool | None = None
    docs_enabled: bool | None = None


class GoogleWorkspaceOAuthStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    services: list[GoogleWorkspaceServiceKey] = Field(min_length=1)


class GoogleWorkspaceOAuthStartRead(BaseModel):
    authorization_url: str
    state_expires_at: datetime
    services: list[GoogleWorkspaceServiceKey]
    scopes: list[str]


class GoogleWorkspaceServiceDefinitionRead(BaseModel):
    key: GoogleWorkspaceServiceKey
    name: str
    description: str
    required_scopes: list[str]
    optional_scopes: list[str]
    implemented: bool
    health_check_supported: bool


class GoogleWorkspaceAccountRead(BaseModel):
    email: str | None
    name: str | None = None
    granted_scopes: list[str]
    token_expires_at: datetime | None
    connection_status: str


class GoogleWorkspaceServiceStatusRead(BaseModel):
    service: GoogleWorkspaceServiceKey
    enabled: bool
    authorized: bool
    status: GoogleWorkspaceHealthStatus
    checked_at: datetime | None = None
    last_error_code: str | None = None


class GoogleWorkspaceStatusRead(BaseModel):
    integration_id: int
    account: GoogleWorkspaceAccountRead
    catalog: list[GoogleWorkspaceServiceDefinitionRead]
    services: list[GoogleWorkspaceServiceStatusRead]

