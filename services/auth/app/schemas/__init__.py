from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(None, max_length=255)

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    password: str | None = Field(None, min_length=8, max_length=100)
    is_active: bool | None = None

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    roles: list[RoleResponse] = []

    class Config:
        from_attributes = True

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
