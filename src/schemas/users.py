from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserCreateSchema(BaseModel):
    login: str
    password: str
    first_name: str
    last_name: str


class UserAuthSchema(BaseModel):
    login: str
    password: str


class UserInDBSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str


class UserUpdateSchema(BaseModel):
    new_login: str
    new_password: str


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
