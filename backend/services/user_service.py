from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models import User
from backend.core import hash_password, verify_password
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Service for user operations."""

    @staticmethod
    async def create_user(session: AsyncSession, email: str, password: str) -> User:
        """Create new user."""
        hashed_password = hash_password(password)
        user = User(email=email, password_hash=hashed_password)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(f"User created: {email}")
        return user

    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
        """Get user by email."""
        result = await session.execute(select(User).where(User.email == email))
        return result.scalars().first()

    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id) -> User | None:
        """Get user by ID."""
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    @staticmethod
    async def verify_user_password(user: User, password: str) -> bool:
        """Verify user password."""
        return verify_password(password, user.password_hash)
