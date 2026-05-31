from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = Field(None, max_length=255)
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
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    manager_id: UUID | None = None
    invited_by: UUID | None = None

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
    role_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr | None = Field(None, max_length=255)
    manager_id: UUID | None = None

    @field_validator("role_name")
    @classmethod
    def validate_role_name(cls, v: str) -> str:
        """Ensure role_name is a valid UserRole enum value."""
        if v not in UserRole:
            raise ValueError("Invalid role name")
        return v


class InvitationResponse(BaseModel):
    id: UUID
    token: str
    email: str | None
    role_name: str
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
