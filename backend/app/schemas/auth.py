from pydantic import BaseModel

from app.schemas.users import ClientProfileCreate


class LoginRequest(BaseModel):
    email: str
    password: str


class ClientRegisterRequest(BaseModel):
    user: "UserCreate"
    client_profile: ClientProfileCreate | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


from app.schemas.users import UserCreate  # noqa: E402

ClientRegisterRequest.model_rebuild()
