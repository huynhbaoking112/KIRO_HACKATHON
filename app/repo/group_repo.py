"""Group repository for database operations."""

from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.models.group import Group


class GroupRepository:
    """Repository for group database operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize GroupRepository with database instance.

        Args:
            db: AsyncIOMotorDatabase instance
        """
        self.collection = db.groups

    async def create(self, name: str, created_by_admin_id: str) -> Group:
        """Create a new group in database.

        Args:
            name: Group display name
            created_by_admin_id: Admin ID who created the group

        Returns:
            Created Group instance
        """
        now = datetime.now(timezone.utc)
        group_data = {
            "name": name,
            "created_by_admin_id": created_by_admin_id,
            "created_at": now,
            "deleted_at": None,
        }

        result = await self.collection.insert_one(group_data)
        group_data["_id"] = str(result.inserted_id)

        return Group(**group_data)

    async def get_by_id(self, group_id: str) -> Optional[Group]:
        """Get a group by ID, excluding soft-deleted records.

        Args:
            group_id: Group ID to search for

        Returns:
            Group instance if found and not deleted, None otherwise
        """
        try:
            object_id = ObjectId(group_id)
        except (TypeError, ValueError):
            return None

        doc = await self.collection.find_one(
            {
                "_id": object_id,
                "deleted_at": None,
            }
        )

        if doc is None:
            return None

        doc["_id"] = str(doc["_id"])
        return Group(**doc)

    async def get_by_ids(self, group_ids: list[str]) -> list[Group]:
        """Get groups by IDs, excluding soft-deleted records.

        Args:
            group_ids: List of group IDs

        Returns:
            List of Group instances found
        """
        object_ids = []
        for group_id in group_ids:
            try:
                object_ids.append(ObjectId(group_id))
            except (TypeError, ValueError):
                continue

        if not object_ids:
            return []

        cursor = self.collection.find(
            {
                "_id": {"$in": object_ids},
                "deleted_at": None,
            }
        )

        groups = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            groups.append(Group(**doc))

        return groups
