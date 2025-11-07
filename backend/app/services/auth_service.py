"""
Authentication service.
"""
from typing import Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models import User, UserCreate, Token
from ..core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["users"]

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if user already exists
        existing_user = await self.collection.find_one({"email": user_data.email})
        if existing_user:
            raise ValueError("User with this email already exists")

        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
        )

        await self.collection.insert_one(user.model_dump())
        return user

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        user_dict = await self.collection.find_one({"email": email})
        if not user_dict:
            return None

        user = User(**user_dict)

        if not verify_password(password, user.password_hash):
            return None

        # Update last login
        await self.collection.update_one(
            {"email": email}, {"$set": {"last_login": datetime.utcnow()}}
        )

        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        user_dict = await self.collection.find_one({"email": email})
        if not user_dict:
            return None
        return User(**user_dict)

    def create_tokens(self, user: User) -> Token:
        """Create access and refresh tokens for a user."""
        token_data = {"sub": user.email, "username": user.username}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
        )
