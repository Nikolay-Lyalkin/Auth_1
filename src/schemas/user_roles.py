from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoleInDBSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str


class RoleCreateSchema(BaseModel):
    name: str = Field(max_length=50)
    description: str = Field(max_length=255)
