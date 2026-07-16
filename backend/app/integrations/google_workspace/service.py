from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.enums import IntegrationProvider
from app.integrations.exceptions import IntegrationError
from app.integrations.google_oauth import GoogleOAuthService
from app.integrations.google_workspace.clients import GoogleDocsClient, GoogleDriveClient, GoogleSheetsClient
from app.integrations.google_workspace.enums import GoogleWorkspaceHealthStatus, GoogleWorkspaceServiceKey
from app.integrations.google_workspace.schemas import (
    GoogleWorkspaceAccountRead,
    GoogleWorkspaceServiceDefinitionRead,
    GoogleWorkspaceServiceStatusRead,
    GoogleWorkspaceSettingsUpdate,
    GoogleWorkspaceStatusRead,
)
from app.integrations.google_workspace.scopes import SERVICE_DEFINITIONS, services_to_scopes
from app.models.integration import GoogleWorkspaceSettings, Integration, IntegrationCredential
from app.models.user import User


class GoogleWorkspaceService:
    def __init__(
        self,
        db: Session,
        *,
        oauth_service: GoogleOAuthService | None = None,
        sheets_client: GoogleSheetsClient | None = None,
        drive_client: GoogleDriveClient | None = None,
        docs_client: GoogleDocsClient | None = None,
    ) -> None:
        self.db = db
        self.oauth_service = oauth_service or GoogleOAuthService(db)
        self.sheets_client = sheets_client or GoogleSheetsClient()
        self.drive_client = drive_client or GoogleDriveClient()
        self.docs_client = docs_client or GoogleDocsClient()

    def status(self, integration_id: int) -> GoogleWorkspaceStatusRead:
        integration = self._integration(integration_id)
        settings = self.settings(integration.id)
        credential = self._credential(integration.id)
        self._sync_authorized(settings, credential.scopes if credential else [])
        self.db.commit()
        return self._status_read(integration, settings, credential)

    def update(self, integration_id: int, payload: GoogleWorkspaceSettingsUpdate) -> GoogleWorkspaceStatusRead:
        integration = self._integration(integration_id)
        settings = self.settings(integration.id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(settings, field, value)
        credential = self._credential(integration.id)
        self._sync_authorized(settings, credential.scopes if credential else [])
        self.db.commit()
        return self._status_read(integration, settings, credential)

    def start_oauth(self, integration_id: int, admin_user: User, services: list[GoogleWorkspaceServiceKey]) -> tuple[str, datetime, list[str]]:
        integration = self._integration(integration_id)
        unique_services = list(dict.fromkeys(services))
        scopes = services_to_scopes(unique_services)
        url, expires_at = self.oauth_service.incremental_authorization_url(
            integration.id,
            admin_user,
            services=[service.value for service in unique_services],
            scopes=scopes,
        )
        return url, expires_at, scopes

    def set_service_enabled(self, integration_id: int, service: GoogleWorkspaceServiceKey, enabled: bool) -> GoogleWorkspaceStatusRead:
        integration = self._integration(integration_id)
        settings = self.settings(integration.id)
        setattr(settings, f"{service.value}_enabled", enabled)
        credential = self._credential(integration.id)
        self._sync_authorized(settings, credential.scopes if credential else [])
        self.db.commit()
        return self._status_read(integration, settings, credential)

    def health(self, integration_id: int, service: GoogleWorkspaceServiceKey | None = None) -> GoogleWorkspaceStatusRead:
        integration = self._integration(integration_id)
        settings = self.settings(integration.id)
        credential = self._credential(integration.id)
        self._sync_authorized(settings, credential.scopes if credential else [])
        services = [service] if service else list(GoogleWorkspaceServiceKey)
        for item in services:
            self._health_one(integration.id, settings, item)
        self.db.commit()
        credential = self._credential(integration.id)
        return self._status_read(integration, settings, credential)

    def update_authorization_from_scopes(self, integration_id: int, scopes: list[str]) -> None:
        settings = self.settings(integration_id)
        self._sync_authorized(settings, scopes)
        self.db.flush()

    def settings(self, integration_id: int) -> GoogleWorkspaceSettings:
        settings = self.db.scalar(select(GoogleWorkspaceSettings).where(GoogleWorkspaceSettings.integration_id == integration_id))
        if settings:
            return settings
        settings = GoogleWorkspaceSettings(integration_id=integration_id)
        self.db.add(settings)
        self.db.flush()
        credential = self._credential(integration_id)
        self._sync_authorized(settings, credential.scopes if credential else [])
        return settings

    def _health_one(self, integration_id: int, settings: GoogleWorkspaceSettings, service: GoogleWorkspaceServiceKey) -> None:
        now = datetime.now(UTC)
        setattr(settings, f"last_{service.value}_check_at", now)
        if not getattr(settings, f"{service.value}_enabled"):
            return
        if not getattr(settings, f"{service.value}_authorized"):
            settings.last_error_at = now
            settings.last_error_service = service.value
            settings.last_error_code = "authorization_required"
            return
        try:
            token = self.oauth_service.access_token(integration_id)
            if service == GoogleWorkspaceServiceKey.drive:
                self.drive_client.health_check(access_token=token)
            elif service == GoogleWorkspaceServiceKey.sheets:
                self.sheets_client.health_check(access_token=token)
            elif service == GoogleWorkspaceServiceKey.docs:
                self.docs_client.health_check(access_token=token)
            settings.last_error_code = None
            settings.last_error_service = None
        except IntegrationError as exc:
            settings.last_error_at = now
            settings.last_error_service = service.value
            settings.last_error_code = exc.code
        except Exception:
            settings.last_error_at = now
            settings.last_error_service = service.value
            settings.last_error_code = "google_workspace_unavailable"

    def _status_read(self, integration: Integration, settings: GoogleWorkspaceSettings, credential: IntegrationCredential | None) -> GoogleWorkspaceStatusRead:
        scopes = credential.scopes if credential else []
        return GoogleWorkspaceStatusRead(
            integration_id=integration.id,
            account=GoogleWorkspaceAccountRead(
                email=credential.external_account_email if credential else None,
                granted_scopes=scopes or [],
                token_expires_at=credential.expires_at if credential else None,
                connection_status="connected" if credential else "not_connected",
            ),
            catalog=[
                GoogleWorkspaceServiceDefinitionRead(
                    key=item.key,
                    name=item.name,
                    description=item.description,
                    required_scopes=list(item.required_scopes),
                    optional_scopes=list(item.optional_scopes),
                    implemented=item.implemented,
                    health_check_supported=item.health_check_supported,
                )
                for item in SERVICE_DEFINITIONS.values()
            ],
            services=[self._service_status(settings, service) for service in GoogleWorkspaceServiceKey],
        )

    def _service_status(self, settings: GoogleWorkspaceSettings, service: GoogleWorkspaceServiceKey) -> GoogleWorkspaceServiceStatusRead:
        enabled = bool(getattr(settings, f"{service.value}_enabled"))
        authorized = bool(getattr(settings, f"{service.value}_authorized"))
        checked_at = getattr(settings, f"last_{service.value}_check_at")
        if not enabled:
            status_value = GoogleWorkspaceHealthStatus.disabled
        elif not authorized:
            status_value = GoogleWorkspaceHealthStatus.authorization_required
        elif service in {GoogleWorkspaceServiceKey.sheets, GoogleWorkspaceServiceKey.docs}:
            status_value = GoogleWorkspaceHealthStatus.authorized_not_resource_tested
        elif settings.last_error_service == service.value and settings.last_error_code:
            status_value = GoogleWorkspaceHealthStatus.unavailable
        else:
            status_value = GoogleWorkspaceHealthStatus.healthy
        return GoogleWorkspaceServiceStatusRead(
            service=service,
            enabled=enabled,
            authorized=authorized,
            status=status_value,
            checked_at=checked_at,
            last_error_code=settings.last_error_code if settings.last_error_service == service.value else None,
        )

    @staticmethod
    def _sync_authorized(settings: GoogleWorkspaceSettings, scopes: list[str]) -> None:
        granted = set(scopes or [])
        for service, definition in SERVICE_DEFINITIONS.items():
            setattr(settings, f"{service.value}_authorized", set(definition.required_scopes).issubset(granted))

    def _integration(self, integration_id: int) -> Integration:
        integration = self.db.get(Integration, integration_id)
        if not integration:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
        if integration.provider != IntegrationProvider.google_meet:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Google Workspace requires the Google integration")
        return integration

    def _credential(self, integration_id: int) -> IntegrationCredential | None:
        return self.db.scalar(
            select(IntegrationCredential).where(
                IntegrationCredential.integration_id == integration_id,
                IntegrationCredential.credential_type == "google_oauth",
                IntegrationCredential.revoked_at.is_(None),
            )
        )
