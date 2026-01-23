"""
Minimal user manager for testing purposes.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import uuid4

from config.settings import settings

logger = logging.getLogger(__name__)


class UserManager:
    """Minimal user manager for testing."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Mock user database
        self.users = {
            "test_user": {
                "id": "test_user",
                "email": "test@example.com",
                "username": "testuser",
                "full_name": "Test User",
                "role": "user",
                "is_active": True,
                "created_at": datetime.now() - timedelta(days=30),
                "subscription_end": datetime.now() + timedelta(days=15),
                "monthly_usage": {"audio_uploads": 5, "processing_minutes": 120},
                "hashed_password": "mock_hashed_password",
            }
        }
        # Mock sessions
        self.sessions = {}

    async def register_user(
        self, email: str, username: str, password: str, full_name: Optional[str] = None
    ) -> Dict:
        """Register a new user (mock implementation)."""
        self.logger.info(f"Registering new user: {email} ({username})")

        # Check if user already exists
        for user in self.users.values():
            if user["email"] == email:
                raise ValueError("User with this email already exists")
            if user["username"] == username:
                raise ValueError("User with this username already exists")

        # Create new user
        user_id = str(uuid4())
        new_user = {
            "id": user_id,
            "email": email,
            "username": username,
            "full_name": full_name,
            "role": "user",
            "is_active": True,
            "created_at": datetime.now(),
            "subscription_end": None,
            "monthly_usage": {"audio_uploads": 0, "processing_minutes": 0},
            "hashed_password": f"mock_hash_{password}",
        }

        self.users[user_id] = new_user

        return {
            "user_id": user_id,
            "email": email,
            "username": username,
            "message": "User registered successfully",
        }

    async def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate a user (mock implementation)."""
        self.logger.info(f"Authenticating user: {email}")

        # Find user by email
        user = None
        for u in self.users.values():
            if u["email"] == email:
                user = u
                break

        if not user:
            return None

        # Mock password check
        if password != "password123":  # Hardcoded for testing
            return None

        # Create session
        session_id = str(uuid4())
        self.sessions[session_id] = {
            "user_id": user["id"],
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=1),
        }

        return {
            "user_id": user["id"],
            "email": user["email"],
            "username": user["username"],
            "role": user["role"],
            "access_token": session_id,
            "token_type": "bearer",
            "expires_in": 3600,
        }

    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID (mock implementation)."""
        user = self.users.get(user_id)
        if not user:
            return None

        # Return user data without sensitive information
        return {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
            "is_active": user["is_active"],
            "created_at": user["created_at"],
            "subscription_end": user["subscription_end"],
            "monthly_usage": user["monthly_usage"],
        }

    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email (mock implementation)."""
        for user in self.users.values():
            if user["email"] == email:
                return {
                    "id": user["id"],
                    "email": user["email"],
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "role": user["role"],
                    "is_active": user["is_active"],
                    "created_at": user["created_at"],
                    "subscription_end": user["subscription_end"],
                    "monthly_usage": user["monthly_usage"],
                }
        return None

    async def update_user_profile(
        self, user_id: str, full_name: Optional[str] = None
    ) -> bool:
        """Update user profile (mock implementation)."""
        user = self.users.get(user_id)
        if not user:
            return False

        if full_name is not None:
            user["full_name"] = full_name

        return True

    async def update_user_usage(
        self, user_id: str, uploads: int = 0, minutes: int = 0
    ) -> bool:
        """Update user usage statistics (mock implementation)."""
        user = self.users.get(user_id)
        if not user:
            return False

        user["monthly_usage"]["audio_uploads"] += uploads
        user["monthly_usage"]["processing_minutes"] += minutes

        return True

    async def validate_token(self, token: str) -> Optional[Dict]:
        """Validate authentication token (mock implementation)."""
        session = self.sessions.get(token)
        if not session:
            return None

        # Check if session is expired
        if datetime.now() > session["expires_at"]:
            del self.sessions[token]
            return None

        # Get user data
        user = await self.get_user_by_id(session["user_id"])
        if not user:
            return None

        return user

    async def refresh_token(self, old_token: str) -> Optional[Dict]:
        """Refresh authentication token (mock implementation)."""
        session = self.sessions.get(old_token)
        if not session:
            return None

        # Create new session
        new_token = str(uuid4())
        self.sessions[new_token] = {
            "user_id": session["user_id"],
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=1),
        }

        # Remove old session
        del self.sessions[old_token]

        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_in": 3600,
        }

    async def logout(self, token: str) -> bool:
        """Logout user (mock implementation)."""
        if token in self.sessions:
            del self.sessions[token]
            return True
        return False

    async def get_user_subscription(self, user_id: str) -> Optional[Dict]:
        """Get user subscription (mock implementation)."""
        user = self.users.get(user_id)
        if not user:
            return None

        if not user["subscription_end"]:
            return None

        return {
            "user_id": user_id,
            "plan_id": "premium",
            "plan_name": "Premium Plan",
            "price_per_month": settings.SUBSCRIPTION_PRICE_RUB,
            "start_date": user["subscription_end"] - timedelta(days=30),
            "end_date": user["subscription_end"],
            "auto_renew": True,
            "status": "active",
        }

    async def update_subscription(
        self, user_id: str, end_date: datetime, plan_id: str = "premium"
    ) -> bool:
        """Update user subscription (mock implementation)."""
        user = self.users.get(user_id)
        if not user:
            return False

        user["subscription_end"] = end_date
        return True
