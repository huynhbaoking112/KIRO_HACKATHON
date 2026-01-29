"""Group member repository for database operations."""

from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.models.group_member import GroupMember


class GroupMemberRepository:
    """Repository for group membership operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize GroupMemberRepository with database instance.

        Args:
            db: AsyncIOMotorDatabase instance
        """
        self.collection = db.group_members

    async def get_by_group_user(
        self, group_id: str, user_id: str
    ) -> Optional[GroupMember]:
        """Get membership record by group and user.

        Args:
            group_id: Group ID
            user_id: User ID

        Returns:
            GroupMember instance if found, None otherwise
        """
        doc = await self.collection.find_one(
            {
                "group_id": group_id,
                "user_id": user_id,
            }
        )

        if doc is None:
            return None

        doc["_id"] = str(doc["_id"])
        return GroupMember(**doc)

    async def upsert_active_member(
        self, group_id: str, user_id: str, admin_id: str
    ) -> GroupMember:
        """Ensure a user is an active member of a group.

        If membership exists and is active, returns existing record.
        If membership exists but removed, re-activates it.
        If membership does not exist, creates a new record.

        Args:
            group_id: Group ID
            user_id: User ID
            admin_id: Admin performing the add

        Returns:
            Active GroupMember record
        """
        existing = await self.get_by_group_user(group_id, user_id)
        if existing is not None and existing.removed_at is None:
            return existing

        now = datetime.now(timezone.utc)
        update = {
            "$set": {
                "group_id": group_id,
                "user_id": user_id,
                "joined_at": now,
                "removed_at": None,
                "added_by_admin_id": admin_id,
                "removed_by_admin_id": None,
                "updated_at": now,
            }
        }

        result = await self.collection.find_one_and_update(
            {"group_id": group_id, "user_id": user_id},
            update,
            upsert=True,
            return_document=True,
        )

        if result is None:
            # Fallback: fetch after upsert
            result = await self.collection.find_one(
                {"group_id": group_id, "user_id": user_id}
            )

        result["_id"] = str(result["_id"])
        return GroupMember(**result)

    async def set_removed(
        self, group_id: str, user_id: str, admin_id: str
    ) -> Optional[GroupMember]:
        """Mark a user as removed from a group.

        Idempotent: if already removed, returns existing record.

        Args:
            group_id: Group ID
            user_id: User ID
            admin_id: Admin performing the removal

        Returns:
            Updated GroupMember record, or None if membership doesn't exist
        """
        existing = await self.get_by_group_user(group_id, user_id)
        if existing is None:
            return None
        if existing.removed_at is not None:
            return existing

        now = datetime.now(timezone.utc)
        result = await self.collection.find_one_and_update(
            {
                "group_id": group_id,
                "user_id": user_id,
            },
            {
                "$set": {
                    "removed_at": now,
                    "removed_by_admin_id": admin_id,
                    "updated_at": now,
                }
            },
            return_document=True,
        )

        if result is None:
            return None

        result["_id"] = str(result["_id"])
        return GroupMember(**result)

    async def is_active_member(self, group_id: str, user_id: str) -> bool:
        """Check if a user is an active member of a group."""
        doc = await self.collection.find_one(
            {
                "group_id": group_id,
                "user_id": user_id,
                "removed_at": None,
            }
        )
        return doc is not None

    async def list_active_group_ids_for_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int | None = 20,
    ) -> list[str]:
        """List active group IDs for a user with pagination."""
        cursor = (
            self.collection.find(
                {
                    "user_id": user_id,
                    "removed_at": None,
                }
            )
            .skip(skip)
        )
        if limit is not None:
            cursor = cursor.limit(limit)

        group_ids: list[str] = []
        async for doc in cursor:
            group_ids.append(doc["group_id"])

        return group_ids

    async def list_groups_for_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[GroupMember]:
        """List active group memberships for a user with pagination."""
        cursor = (
            self.collection.find(
                {
                    "user_id": user_id,
                    "removed_at": None,
                }
            )
            .skip(skip)
            .limit(limit)
        )

        members: list[GroupMember] = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            members.append(GroupMember(**doc))

        return members

    async def count_active_groups_for_user(self, user_id: str) -> int:
        """Count active group memberships for a user."""
        return await self.collection.count_documents(
            {
                "user_id": user_id,
                "removed_at": None,
            }
        )
