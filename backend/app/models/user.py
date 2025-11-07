"""
User data models.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    """User model."""
    email: EmailStr
    username: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = True
    is_admin: bool = False


class UserCreate(BaseModel):
    """User creation model."""
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response model (excludes password)."""
    email: EmailStr
    username: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool
    is_admin: bool


class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data model."""
    email: Optional[str] = None
