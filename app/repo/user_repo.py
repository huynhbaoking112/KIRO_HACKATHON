"""User repository for database operations."""

from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.models.user import User, UserRole


class UserRepository:
    """Repository for user database operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize UserRepository with database instance.

        Args:
            db: AsyncIOMotorDatabase instance
        """
        self.collection = db.users

    async def create(
        self,
        email: str,
        hashed_password: str,
        role: UserRole = UserRole.USER,
        is_active: bool = True,
    ) -> User:
        """Create a new user in database.

        Args:
            email: User email address
            hashed_password: Bcrypt hashed password
            role: User role (default: USER)
            is_active: Whether user is active (default: True)

        Returns:
            Created User instance
        """
        now = datetime.now(timezone.utc)
        user_data = {
            "email": email,
            "hashed_password": hashed_password,
            "role": role.value,
            "is_active": is_active,
            "created_at": now,
            "updated_at": now,
        }

        result = await self.collection.insert_one(user_data)
        user_data["_id"] = str(result.inserted_id)

        return User(**user_data)

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email.

        Args:
            email: Email address to search for

        Returns:
            User instance if found, None otherwise
        """
        user_doc = await self.collection.find_one({"email": email})

        if user_doc is None:
            return None

        user_doc["_id"] = str(user_doc["_id"])
        return User(**user_doc)

    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID.

        Args:
            user_id: User ID to search for

        Returns:
            User instance if found, None otherwise
        """
        try:
            object_id = ObjectId(user_id)
        except (TypeError, ValueError):
            return None

        user_doc = await self.collection.find_one({"_id": object_id})

        if user_doc is None:
            return None

        user_doc["_id"] = str(user_doc["_id"])
        return User(**user_doc)
