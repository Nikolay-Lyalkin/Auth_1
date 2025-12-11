from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LoginHistoryResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    ip_address: str
    user_agent: str | None
    device_type: str | None


class LoginHistoryCreateSchema(BaseModel):
    user_id: UUID
    ip_address: str = Field(..., max_length=45)
    user_agent: str | None = Field(max_length=512)
    device_type: str | None = Field(max_length=50)
    login_status: str = Field("success", max_length=20)
