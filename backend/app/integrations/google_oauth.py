from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import secrets
from typing import Protocol
from urllib.parse import urlencode

import httpx
import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.integrations.crypto import TokenCipher
from app.integrations.enums import IntegrationProvider, IntegrationStatus
from app.integrations.exceptions import IntegrationConfigurationError, IntegrationError, IntegrationNotFoundError
from app.models.audit_log import AuditLog
from app.models.integration import Integration, IntegrationCredential, IntegrationOAuthState
from app.models.user import User

GOOGLE_OAUTH_CREDENTIAL_TYPE = "google_oauth"


class GoogleOAuthError(IntegrationError):
    pass


@dataclass
class GoogleTokenResponse:
    access_token: str
    refresh_token: str | None
    token_type: str
    expires_in: int
    scopes: list[str]
    id_token: str | None = None


@dataclass
class GoogleAccountInfo:
    account_id: str | None
    email: str | None


class GoogleOAuthClient(Protocol):
    def build_authorization_url(self, *, state: str, settings: Settings, scopes: list[str] | None = None, incremental: bool = False, prompt_consent: bool = True) -> str:
        ...

    def exchange_code(self, *, code: str, settings: Settings) -> GoogleTokenResponse:
        ...

    def refresh_access_token(self, *, refresh_token: str, settings: Settings) -> GoogleTokenResponse:
        ...

    def revoke_token(self, *, token: str, settings: Settings) -> None:
        ...

    def fetch_account_info(self, *, access_token: str) -> GoogleAccountInfo:
        ...


class GoogleOAuthHTTPClient:
    authorization_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    token_endpoint = "https://oauth2.googleapis.com/token"
    revoke_endpoint = "https://oauth2.googleapis.com/revoke"
    token_info_endpoint = "https://oauth2.googleapis.com/tokeninfo"

    def build_authorization_url(self, *, state: str, settings: Settings, scopes: list[str] | None = None, incremental: bool = False, prompt_consent: bool = True) -> str:
        _ensure_oauth_settings(settings)
        params = {
            "client_id": settings.google_oauth_client_id,
            "redirect_uri": settings.google_oauth_redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes or settings.google_oauth_scopes),
            "access_type": "offline",
            "state": state,
        }
        if incremental:
            params["include_granted_scopes"] = "true"
        if prompt_consent:
            params["prompt"] = "consent"
        query = urlencode(params)
        return f"{self.authorization_endpoint}?{query}"

    def exchange_code(self, *, code: str, settings: Settings) -> GoogleTokenResponse:
        _ensure_oauth_settings(settings)
        response = httpx.post(
            self.token_endpoint,
            data={
                "code": code,
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "redirect_uri": settings.google_oauth_redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        if response.status_code >= 400:
            raise GoogleOAuthError("No pudimos intercambiar el codigo OAuth", code="google_oauth_exchange_failed")
        data = response.json()
        return _token_response_from_google(data, settings.google_oauth_scopes)

    def refresh_access_token(self, *, refresh_token: str, settings: Settings) -> GoogleTokenResponse:
        _ensure_oauth_settings(settings)
        response = httpx.post(
            self.token_endpoint,
            data={
                "refresh_token": refresh_token,
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "grant_type": "refresh_token",
            },
            timeout=10,
        )
        if response.status_code >= 400:
            raise GoogleOAuthError("No pudimos refrescar la autorizacion Google", code="google_oauth_refresh_failed")
        return _token_response_from_google(response.json(), settings.google_oauth_scopes, fallback_refresh_token=refresh_token)

    def revoke_token(self, *, token: str, settings: Settings) -> None:
        _ensure_oauth_settings(settings)
        httpx.post(self.revoke_endpoint, params={"token": token}, timeout=10)

    def fetch_account_info(self, *, access_token: str) -> GoogleAccountInfo:
        response = httpx.get(self.token_info_endpoint, params={"access_token": access_token}, timeout=10)
        if response.status_code >= 400:
            return GoogleAccountInfo(account_id=None, email=None)
        data = response.json()
        return GoogleAccountInfo(account_id=data.get("sub"), email=data.get("email"))


class GoogleOAuthService:
    def __init__(
        self,
        db: Session,
        *,
        oauth_client: GoogleOAuthClient | None = None,
        app_settings: Settings | None = None,
        now: datetime | None = None,
    ) -> None:
        self.db = db
        self.oauth_client = oauth_client or GoogleOAuthHTTPClient()
        self.settings = app_settings or settings
        self.now = now

    def authorization_url(self, integration_id: int, admin_user: User) -> tuple[str, datetime]:
        integration = self._get_google_integration(integration_id)
        _ensure_oauth_settings(self.settings)
        state, expires_at = self._create_state(integration, admin_user)
        url = self.oauth_client.build_authorization_url(state=state, settings=self.settings)
        self._audit(admin_user, "google_oauth_authorization_started", integration, {"result": "started"})
        self.db.commit()
        return url, expires_at

    def incremental_authorization_url(self, integration_id: int, admin_user: User, *, services: list[str], scopes: list[str]) -> tuple[str, datetime]:
        integration = self._get_google_integration(integration_id)
        _ensure_oauth_settings(self.settings)
        credential = self._active_credential(integration.id)
        all_scopes = list(dict.fromkeys([*(credential.scopes if credential else []), *scopes]))
        state, expires_at = self._create_state(integration, admin_user, requested_services=services)
        url = self.oauth_client.build_authorization_url(
            state=state,
            settings=self.settings,
            scopes=all_scopes,
            incremental=True,
            prompt_consent=credential is None or not credential.encrypted_refresh_token,
        )
        self._audit(admin_user, "google_workspace_oauth_authorization_started", integration, {"result": "started", "services": services})
        self.db.commit()
        return url, expires_at

    def callback(self, *, code: str, state: str) -> IntegrationCredential:
        state_row = self._consume_state(state)
        integration = self._get_google_integration(state_row.integration_id)
        admin_user = self.db.get(User, state_row.admin_user_id)
        try:
            token_response = self.oauth_client.exchange_code(code=code, settings=self.settings)
            account = self.oauth_client.fetch_account_info(access_token=token_response.access_token)
            credential = self._upsert_credential(integration, token_response, account)
            from app.integrations.google_workspace.service import GoogleWorkspaceService

            GoogleWorkspaceService(self.db, oauth_service=self).update_authorization_from_scopes(integration.id, credential.scopes or [])
            integration.status = IntegrationStatus.configured
            integration.last_error_message = None
            if admin_user:
                self._audit(admin_user, "google_oauth_authorization_completed", integration, {"result": "connected"})
            self.db.commit()
            self.db.refresh(credential)
            return credential
        except IntegrationError as exc:
            integration.status = IntegrationStatus.error
            integration.last_error_message = exc.message
            if admin_user:
                self._audit(admin_user, "google_oauth_authorization_failed", integration, {"result": "failed", "code": exc.code})
            self.db.commit()
            raise

    def status(self, integration_id: int) -> dict:
        integration = self._get_google_integration(integration_id)
        credential = self._active_credential(integration.id)
        if not credential:
            return {"status": "not_connected", "provider": IntegrationProvider.google_meet, "connected": False}
        now = self._now()
        status = "connected"
        if credential.revoked_at:
            status = "revoked"
        elif credential.expires_at and credential.expires_at <= now:
            status = "expired"
        elif credential.last_error_message:
            status = "error"
        return {
            "status": status,
            "provider": IntegrationProvider.google_meet,
            "connected": status == "connected",
            "external_account_email": credential.external_account_email,
            "external_account_id": credential.external_account_id,
            "scopes": credential.scopes or [],
            "authorized_at": credential.authorized_at,
            "expires_at": credential.expires_at,
            "last_refresh_at": credential.last_refresh_at,
            "revoked_at": credential.revoked_at,
            "last_error_message": credential.last_error_message,
        }

    def refresh(self, integration_id: int, admin_user: User) -> IntegrationCredential:
        integration = self._get_google_integration(integration_id)
        credential = self._require_active_credential(integration.id)
        if not credential.encrypted_refresh_token:
            raise GoogleOAuthError("La autorizacion Google no tiene refresh token", code="google_refresh_token_missing")
        cipher = TokenCipher(self.settings.google_token_encryption_key)
        refresh_token = cipher.decrypt(credential.encrypted_refresh_token)
        response = self.oauth_client.refresh_access_token(refresh_token=refresh_token, settings=self.settings)
        credential.encrypted_access_token = cipher.encrypt(response.access_token)
        if response.refresh_token:
            credential.encrypted_refresh_token = cipher.encrypt(response.refresh_token)
        credential.token_type = response.token_type
        credential.expires_at = self._now() + timedelta(seconds=response.expires_in)
        credential.scopes = response.scopes
        credential.last_refresh_at = self._now()
        credential.last_error_message = None
        self._audit(admin_user, "google_oauth_token_refreshed", integration, {"result": "refreshed"})
        self.db.commit()
        self.db.refresh(credential)
        return credential

    def access_token(self, integration_id: int) -> str:
        integration = self._get_google_integration(integration_id)
        credential = self._require_active_credential(integration.id)
        cipher = TokenCipher(self.settings.google_token_encryption_key)
        if credential.expires_at and credential.expires_at <= self._now() + timedelta(minutes=2):
            if not credential.encrypted_refresh_token:
                raise GoogleOAuthError("La autorizacion Google no tiene refresh token", code="google_refresh_token_missing")
            refresh_token = cipher.decrypt(credential.encrypted_refresh_token)
            response = self.oauth_client.refresh_access_token(refresh_token=refresh_token, settings=self.settings)
            credential.encrypted_access_token = cipher.encrypt(response.access_token)
            if response.refresh_token:
                credential.encrypted_refresh_token = cipher.encrypt(response.refresh_token)
            credential.token_type = response.token_type
            credential.expires_at = self._now() + timedelta(seconds=response.expires_in)
            credential.scopes = response.scopes
            credential.last_refresh_at = self._now()
            credential.last_error_message = None
            self.db.commit()
            return response.access_token
        if not credential.encrypted_access_token:
            raise GoogleOAuthError("La integracion Google no esta conectada", code="google_oauth_not_connected")
        return cipher.decrypt(credential.encrypted_access_token)

    def disconnect(self, integration_id: int, admin_user: User) -> None:
        integration = self._get_google_integration(integration_id)
        credential = self._active_credential(integration.id)
        if credential:
            refresh_token = None
            if credential.encrypted_refresh_token:
                try:
                    refresh_token = TokenCipher(self.settings.google_token_encryption_key).decrypt(credential.encrypted_refresh_token)
                    self.oauth_client.revoke_token(token=refresh_token, settings=self.settings)
                except IntegrationError:
                    pass
            credential.encrypted_access_token = None
            credential.encrypted_refresh_token = None
            credential.revoked_at = self._now()
            credential.last_error_message = None
        integration.enabled = False
        integration.status = IntegrationStatus.configured
        self._audit(admin_user, "google_oauth_disconnected", integration, {"result": "disconnected"})
        self.db.commit()

    def _create_state(self, integration: Integration, admin_user: User, requested_services: list[str] | None = None) -> tuple[str, datetime]:
        nonce = secrets.token_urlsafe(32)
        expires_at = self._now() + timedelta(seconds=self.settings.google_oauth_state_ttl_seconds)
        payload = {
            "integration_id": integration.id,
            "admin_user_id": admin_user.id,
            "provider": IntegrationProvider.google_meet.value,
            "nonce": nonce,
            "services": requested_services or [],
            "exp": int(expires_at.timestamp()),
        }
        token = jwt.encode(payload, self.settings.secret_key, algorithm="HS256")
        self.db.add(
            IntegrationOAuthState(
                integration_id=integration.id,
                admin_user_id=admin_user.id,
                provider=IntegrationProvider.google_meet,
                nonce_hash=_hash_nonce(nonce),
                requested_services=requested_services or [],
                expires_at=expires_at,
            )
        )
        return token, expires_at

    def _consume_state(self, state: str) -> IntegrationOAuthState:
        try:
            payload = jwt.decode(state, self.settings.secret_key, algorithms=["HS256"])
        except jwt.PyJWTError as exc:
            raise GoogleOAuthError("La solicitud de autorizacion expiro o no es valida", code="google_oauth_state_invalid") from exc
        if payload.get("provider") != IntegrationProvider.google_meet.value:
            raise GoogleOAuthError("La solicitud de autorizacion no corresponde a Google Meet", code="google_oauth_state_provider_invalid")
        nonce = payload.get("nonce")
        integration_id = payload.get("integration_id")
        admin_user_id = payload.get("admin_user_id")
        if not nonce or not integration_id or not admin_user_id:
            raise GoogleOAuthError("La solicitud de autorizacion no es valida", code="google_oauth_state_invalid")
        state_row = self.db.scalar(
            select(IntegrationOAuthState).where(
                IntegrationOAuthState.integration_id == integration_id,
                IntegrationOAuthState.admin_user_id == admin_user_id,
                IntegrationOAuthState.nonce_hash == _hash_nonce(str(nonce)),
            )
        )
        if not state_row or state_row.consumed_at is not None or state_row.expires_at <= self._now():
            raise GoogleOAuthError("La solicitud de autorizacion expiro o ya fue utilizada", code="google_oauth_state_consumed")
        state_row.consumed_at = self._now()
        self.db.flush()
        return state_row

    def _upsert_credential(self, integration: Integration, token_response: GoogleTokenResponse, account: GoogleAccountInfo) -> IntegrationCredential:
        cipher = TokenCipher(self.settings.google_token_encryption_key)
        credential = self._active_credential(integration.id)
        if not credential:
            credential = IntegrationCredential(integration_id=integration.id, credential_type=GOOGLE_OAUTH_CREDENTIAL_TYPE)
            self.db.add(credential)
        credential.encrypted_access_token = cipher.encrypt(token_response.access_token)
        credential.encrypted_refresh_token = cipher.encrypt(token_response.refresh_token) if token_response.refresh_token else credential.encrypted_refresh_token
        credential.token_type = token_response.token_type
        credential.expires_at = self._now() + timedelta(seconds=token_response.expires_in)
        credential.scopes = token_response.scopes
        credential.external_account_id = account.account_id
        credential.external_account_email = account.email
        credential.authorized_at = self._now()
        credential.revoked_at = None
        credential.last_error_message = None
        self.db.flush()
        return credential

    def _get_google_integration(self, integration_id: int) -> Integration:
        integration = self.db.get(Integration, integration_id)
        if not integration:
            raise IntegrationNotFoundError("Integracion no encontrada", code="integration_not_found")
        if integration.provider != IntegrationProvider.google_meet:
            raise GoogleOAuthError("La autorizacion Google solo esta disponible para Google Meet", code="google_oauth_provider_required")
        return integration

    def _active_credential(self, integration_id: int) -> IntegrationCredential | None:
        return self.db.scalar(
            select(IntegrationCredential).where(
                IntegrationCredential.integration_id == integration_id,
                IntegrationCredential.credential_type == GOOGLE_OAUTH_CREDENTIAL_TYPE,
                IntegrationCredential.revoked_at.is_(None),
            )
        )

    def _require_active_credential(self, integration_id: int) -> IntegrationCredential:
        credential = self._active_credential(integration_id)
        if not credential:
            raise GoogleOAuthError("La integracion Google no esta conectada", code="google_oauth_not_connected")
        return credential

    def _audit(self, admin_user: User, action: str, integration: Integration, metadata: dict) -> None:
        self.db.add(
            AuditLog(
                user_id=admin_user.id,
                action=action,
                entity_name="Integration",
                entity_id=str(integration.id),
                metadata_json={
                    "integration_id": integration.id,
                    "provider": IntegrationProvider.google_meet.value,
                    **metadata,
                },
                created_at=self._now(),
            )
        )

    def _now(self) -> datetime:
        return self.now or datetime.now(UTC)


def _ensure_oauth_settings(app_settings: Settings) -> None:
    missing = []
    if not app_settings.google_oauth_client_id:
        missing.append("GOOGLE_OAUTH_CLIENT_ID")
    if not app_settings.google_oauth_client_secret:
        missing.append("GOOGLE_OAUTH_CLIENT_SECRET")
    if not app_settings.google_oauth_redirect_uri:
        missing.append("GOOGLE_OAUTH_REDIRECT_URI")
    if not app_settings.google_token_encryption_key:
        missing.append("GOOGLE_TOKEN_ENCRYPTION_KEY")
    if missing:
        raise IntegrationConfigurationError("Google OAuth no esta configurado", code="google_oauth_not_configured")


def _hash_nonce(nonce: str) -> str:
    return hashlib.sha256(nonce.encode()).hexdigest()


def _token_response_from_google(data: dict, fallback_scopes: list[str], *, fallback_refresh_token: str | None = None) -> GoogleTokenResponse:
    access_token = data.get("access_token")
    if not access_token:
        raise GoogleOAuthError("Google no devolvio access token", code="google_oauth_access_token_missing")
    scope_value = data.get("scope")
    scopes = scope_value.split() if isinstance(scope_value, str) and scope_value else fallback_scopes
    return GoogleTokenResponse(
        access_token=access_token,
        refresh_token=data.get("refresh_token") or fallback_refresh_token,
        token_type=data.get("token_type", "Bearer"),
        expires_in=int(data.get("expires_in", 3600)),
        scopes=scopes,
        id_token=data.get("id_token"),
    )
