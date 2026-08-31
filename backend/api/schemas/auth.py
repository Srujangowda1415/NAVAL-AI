from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

Role = Literal["viewer", "analyst", "admin"]


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    # Only an existing admin can create anything other than "viewer" — see
    # api/routes/auth.py register(). Self-registration always yields "viewer".


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: Role
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoleUpdate(BaseModel):
    role: Role
