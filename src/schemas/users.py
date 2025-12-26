from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserCreateSchema(BaseModel):
    login: str
    email: str
    password: str
    password_again: str
    first_name: str
    last_name: str


class UserAuthSchema(BaseModel):
    email: str
    password: str


class UserInDBSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    login: str
    email: str
    password: str
    first_name: str
    last_name: str
    role_id: UUID
    created_at: datetime


class UserUpdateSchema(BaseModel):
    new_login: str
    new_password: str


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str


class AuthResponse(BaseModel):
    token: "TokenSchema"
    user: "UserSchema"

    class Config:
        arbitrary_types_allowed = True
