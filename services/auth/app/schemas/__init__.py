from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(None, max_length=255)


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    password: str | None = Field(None, min_length=8, max_length=100)
    is_active: bool | None = None
    manager_id: UUID | None = None

    @field_validator("manager_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        """Convert empty string to None for manager_id."""
        if v == "":
            return None
        return v


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    manager_id: UUID | None = None
    invited_by: UUID | None = None
    roles: list[RoleResponse] = []

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None
    type: str | None = None
    jti: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class InvitationCreate(BaseModel):
    role_id: UUID
    email: str | None = Field(None, max_length=255)
    manager_id: UUID | None = None


class InvitationResponse(BaseModel):
    id: UUID
    token: str
    email: str | None
    role_id: UUID
    manager_id: UUID | None
    created_by: UUID | None
    used: bool
    used_by: UUID | None
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegisterWithInvitation(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    invitation_token: str | None = Field(None, min_length=1)
