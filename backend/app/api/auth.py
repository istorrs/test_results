"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from ..core.database import get_database
from ..services.auth_service import AuthService
from ..models import UserCreate, UserLogin, UserResponse, Token
from .dependencies import get_current_user
from ..models import User

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user."""
    db = get_database()
    auth_service = AuthService(db)

    try:
        user = await auth_service.create_user(user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return UserResponse(
        email=user.email,
        username=user.username,
        created_at=user.created_at,
        last_login=user.last_login,
        is_active=user.is_active,
        is_admin=user.is_admin,
    )


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login and get access tokens."""
    db = get_database()
    auth_service = AuthService(db)

    user = await auth_service.authenticate_user(login_data.email, login_data.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = auth_service.create_tokens(user)
    return tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        email=current_user.email,
        username=current_user.username,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
    )
