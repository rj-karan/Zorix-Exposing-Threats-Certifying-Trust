from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from backend.database import get_db
from backend.schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from backend.services import UserService
from backend.core import create_access_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate, session: AsyncSession = Depends(get_db)):
    """Register new user."""
    # Check if user already exists
    existing_user = await UserService.get_user_by_email(session, user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = await UserService.create_user(session, user_create.email, user_create.password)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(user_login: UserLogin, session: AsyncSession = Depends(get_db)):
    """Login user and return JWT token."""
    # Get user by email
    user = await UserService.get_user_by_email(session, user_login.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not await UserService.verify_user_password(user, user_login.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=30),
    )

    return TokenResponse(access_token=access_token, user=user)
