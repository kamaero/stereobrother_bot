"""
User repository for database operations.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import User, UserRole


class UserRepository:
    """Repository for User model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        email: str,
        username: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.USER,
    ) -> User:
        """
        Create a new user.

        Args:
            email: User email
            username: Username
            hashed_password: Hashed password
            full_name: Full name (optional)
            role: User role

        Returns:
            Created user instance
        """
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            is_active=True,
            is_verified=False,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User instance or None
        """
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User instance or None
        """
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username

        Returns:
            User instance or None
        """
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> List[User]:
        """
        Get all users with pagination.

        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            is_active: Filter by active status (optional)

        Returns:
            List of users
        """
        query = select(User)

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        user_id: int,
        **kwargs,
    ) -> Optional[User]:
        """
        Update user fields.

        Args:
            user_id: User ID
            **kwargs: Fields to update

        Returns:
            Updated user instance or None
        """
        # Remove None values
        update_data = {k: v for k, v in kwargs.items() if v is not None}

        if not update_data:
            return await self.get_by_id(user_id)

        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()

        await self.session.execute(
            update(User).where(User.id == user_id).values(**update_data)
        )
        await self.session.flush()

        return await self.get_by_id(user_id)

    async def update_last_login(self, user_id: int) -> None:
        """
        Update user's last login timestamp.

        Args:
            user_id: User ID
        """
        await self.session.execute(
            update(User).where(User.id == user_id).values(last_login=datetime.utcnow())
        )
        await self.session.flush()

    async def update_usage_stats(
        self,
        user_id: int,
        uploads: int = 0,
        processing_minutes: int = 0,
    ) -> None:
        """
        Update user's usage statistics.

        Args:
            user_id: User ID
            uploads: Number of uploads to add
            processing_minutes: Processing minutes to add
        """
        user = await self.get_by_id(user_id)
        if not user:
            return

        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                total_uploads=User.total_uploads + uploads,
                total_processing_minutes=User.total_processing_minutes
                + processing_minutes,
                monthly_uploads=User.monthly_uploads + uploads,
                monthly_processing_minutes=User.monthly_processing_minutes
                + processing_minutes,
            )
        )
        await self.session.flush()

    async def reset_monthly_stats(self, user_id: int) -> None:
        """
        Reset user's monthly statistics.

        Args:
            user_id: User ID
        """
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                monthly_uploads=0,
                monthly_processing_minutes=0,
            )
        )
        await self.session.flush()

    async def update_subscription(
        self,
        user_id: int,
        subscription_end: Optional[datetime],
        role: Optional[UserRole] = None,
    ) -> Optional[User]:
        """
        Update user's subscription.

        Args:
            user_id: User ID
            subscription_end: Subscription end date
            role: New role (optional)

        Returns:
            Updated user instance or None
        """
        update_data = {"subscription_end": subscription_end}

        if role:
            update_data["role"] = role

        return await self.update(user_id, **update_data)

    async def deactivate(self, user_id: int) -> Optional[User]:
        """
        Deactivate a user.

        Args:
            user_id: User ID

        Returns:
            Updated user instance or None
        """
        return await self.update(user_id, is_active=False)

    async def activate(self, user_id: int) -> Optional[User]:
        """
        Activate a user.

        Args:
            user_id: User ID

        Returns:
            Updated user instance or None
        """
        return await self.update(user_id, is_active=True)

    async def verify_email(self, user_id: int) -> Optional[User]:
        """
        Mark user's email as verified.

        Args:
            user_id: User ID

        Returns:
            Updated user instance or None
        """
        return await self.update(user_id, is_verified=True)

    async def delete(self, user_id: int) -> bool:
        """
        Delete a user (soft delete by deactivating).

        Args:
            user_id: User ID

        Returns:
            True if deleted, False otherwise
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False

        await self.deactivate(user_id)
        return True

    async def exists_by_email(self, email: str) -> bool:
        """
        Check if user with email exists.

        Args:
            email: Email to check

        Returns:
            True if exists, False otherwise
        """
        result = await self.session.execute(select(User.id).where(User.email == email))
        return result.scalar_one_or_none() is not None

    async def exists_by_username(self, username: str) -> bool:
        """
        Check if user with username exists.

        Args:
            username: Username to check

        Returns:
            True if exists, False otherwise
        """
        result = await self.session.execute(
            select(User.id).where(User.username == username)
        )
        return result.scalar_one_or_none() is not None

    async def count(self, is_active: Optional[bool] = None) -> int:
        """
        Count users.

        Args:
            is_active: Filter by active status (optional)

        Returns:
            Number of users
        """
        from sqlalchemy import func

        query = select(func.count(User.id))

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_with_subscriptions(self, user_id: int) -> Optional[User]:
        """
        Get user with subscriptions loaded.

        Args:
            user_id: User ID

        Returns:
            User instance with subscriptions or None
        """
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.subscriptions))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_with_audio_files(
        self, user_id: int, limit: int = 10
    ) -> Optional[User]:
        """
        Get user with recent audio files.

        Args:
            user_id: User ID
            limit: Number of recent files to load

        Returns:
            User instance with audio files or None
        """
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.audio_files))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """
        Search users by email, username, or full name.

        Args:
            query: Search query
            skip: Number of users to skip
            limit: Maximum number of users to return

        Returns:
            List of matching users
        """
        search_pattern = f"%{query}%"

        result = await self.session.execute(
            select(User)
            .where(
                (User.email.ilike(search_pattern))
                | (User.username.ilike(search_pattern))
                | (User.full_name.ilike(search_pattern))
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
