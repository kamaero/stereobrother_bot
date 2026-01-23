"""
Authentication service with JWT tokens for StereoBrother Bot.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from src.database.models import User
from src.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for user management and JWT tokens."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if password matches, False otherwise
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Hash a password.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(
        data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.

        Args:
            data: Data to encode in token
            expires_delta: Token expiration time

        Returns:
            JWT token string
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})

        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """
        Create JWT refresh token.

        Args:
            data: Data to encode in token

        Returns:
            JWT refresh token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})

        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """
        Decode and verify JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token data or None if invalid
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.error(f"Error decoding token: {e}")
            return None

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user by email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            User instance if authenticated, None otherwise
        """
        user = await self.user_repo.get_by_email(email)

        if not user:
            logger.warning(f"Authentication failed: user not found - {email}")
            return None

        if not user.is_active:
            logger.warning(f"Authentication failed: user not active - {email}")
            return None

        if not self.verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: invalid password - {email}")
            return None

        # Update last login
        await self.user_repo.update_last_login(user.id)

        logger.info(f"User authenticated successfully: {email}")
        return user

    async def register_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None,
    ) -> User:
        """
        Register a new user.

        Args:
            email: User email
            username: Username
            password: Plain text password
            full_name: Full name (optional)

        Returns:
            Created user instance

        Raises:
            ValueError: If user already exists
        """
        # Check if user already exists
        if await self.user_repo.exists_by_email(email):
            raise ValueError(f"User with email {email} already exists")

        if await self.user_repo.exists_by_username(username):
            raise ValueError(f"User with username {username} already exists")

        # Hash password
        hashed_password = self.get_password_hash(password)

        # Create user
        user = await self.user_repo.create(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
        )

        await self.session.commit()
        logger.info(f"User registered successfully: {email}")

        return user

    async def get_current_user(self, token: str) -> Optional[User]:
        """
        Get current user from JWT token.

        Args:
            token: JWT token string

        Returns:
            User instance or None
        """
        payload = self.decode_token(token)

        if not payload:
            return None

        user_id: Optional[int] = payload.get("sub")
        if not user_id:
            return None

        user = await self.user_repo.get_by_id(int(user_id))

        if not user or not user.is_active:
            return None

        return user

    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Create new access token from refresh token.

        Args:
            refresh_token: Refresh token string

        Returns:
            New access token or None if invalid
        """
        payload = self.decode_token(refresh_token)

        if not payload:
            return None

        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            logger.warning("Invalid token type for refresh")
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        # Verify user still exists and is active
        user = await self.user_repo.get_by_id(int(user_id))
        if not user or not user.is_active:
            return None

        # Create new access token
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )

        return access_token

    async def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password

        Returns:
            True if password changed, False otherwise
        """
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            return False

        # Verify old password
        if not self.verify_password(old_password, user.hashed_password):
            logger.warning(
                f"Password change failed: invalid old password - user {user_id}"
            )
            return False

        # Hash new password
        hashed_password = self.get_password_hash(new_password)

        # Update password
        await self.user_repo.update(user_id, hashed_password=hashed_password)
        await self.session.commit()

        logger.info(f"Password changed successfully for user {user_id}")
        return True

    async def reset_password(self, email: str, new_password: str) -> bool:
        """
        Reset user password (for forgot password flow).

        Args:
            email: User email
            new_password: New password

        Returns:
            True if password reset, False otherwise
        """
        user = await self.user_repo.get_by_email(email)

        if not user:
            logger.warning(f"Password reset failed: user not found - {email}")
            return False

        # Hash new password
        hashed_password = self.get_password_hash(new_password)

        # Update password
        await self.user_repo.update(user.id, hashed_password=hashed_password)
        await self.session.commit()

        logger.info(f"Password reset successfully for user {email}")
        return True

    def create_tokens_for_user(self, user: User) -> dict:
        """
        Create access and refresh tokens for user.

        Args:
            user: User instance

        Returns:
            Dictionary with access_token and refresh_token
        """
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )

        refresh_token = self.create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }


__all__ = ["AuthService", "pwd_context"]
