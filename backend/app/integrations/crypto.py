from cryptography.fernet import Fernet, InvalidToken

from app.integrations.exceptions import IntegrationConfigurationError


class TokenCipher:
    def __init__(self, key: str | None) -> None:
        if not key:
            raise IntegrationConfigurationError("La clave de cifrado OAuth no esta configurada", code="oauth_encryption_key_missing")
        try:
            self._fernet = Fernet(key.encode())
        except ValueError as exc:
            raise IntegrationConfigurationError("La clave de cifrado OAuth no es valida", code="oauth_encryption_key_invalid") from exc

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode()).decode()

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode()).decode()
        except InvalidToken as exc:
            raise IntegrationConfigurationError("No pudimos descifrar la credencial OAuth", code="oauth_token_decrypt_failed") from exc
