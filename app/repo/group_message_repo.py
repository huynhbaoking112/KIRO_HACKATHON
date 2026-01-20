"""Group message repository for database operations."""

import base64
import json
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.models.group_message import GroupMessage


class GroupMessageRepository:
    """Repository for group message database operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize GroupMessageRepository with database instance.

        Args:
            db: AsyncIOMotorDatabase instance
        """
        self.collection = db.group_messages

    async def create_message(
        self,
        group_id: str,
        sender_id: str,
        content: str,
        client_msg_id: Optional[str] = None,
    ) -> GroupMessage:
        """Create a new group message in database."""
        now = datetime.now(timezone.utc)
        message_data = {
            "group_id": group_id,
            "sender_id": sender_id,
            "content": content,
            "client_msg_id": client_msg_id,
            "created_at": now,
            "deleted_at": None,
        }

        result = await self.collection.insert_one(message_data)
        message_data["_id"] = str(result.inserted_id)
        return GroupMessage(**message_data)

    async def list_messages(
        self,
        group_id: str,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> tuple[list[GroupMessage], Optional[str]]:
        """List group messages in reverse chronological order with cursor pagination.

        Args:
            group_id: Group ID
            cursor: Optional opaque cursor from previous page
            limit: Max number of messages to return

        Returns:
            Tuple of (messages, next_cursor)
        """
        query = {
            "group_id": group_id,
            "deleted_at": None,
        }

        if cursor:
            cursor_dt, cursor_id = self._decode_cursor(cursor)
            query["$or"] = [
                {"created_at": {"$lt": cursor_dt}},
                {"created_at": cursor_dt, "_id": {"$lt": cursor_id}},
            ]

        cursor_obj = (
            self.collection.find(query)
            .sort([("created_at", -1), ("_id", -1)])
            .limit(limit)
        )

        messages: list[GroupMessage] = []
        async for doc in cursor_obj:
            doc["_id"] = str(doc["_id"])
            messages.append(GroupMessage(**doc))

        next_cursor = None
        if messages:
            last = messages[-1]
            next_cursor = self._encode_cursor(last.created_at, last.id)

        return messages, next_cursor

    @staticmethod
    def _encode_cursor(created_at: datetime, message_id: str) -> str:
        payload = {
            "created_at": created_at.isoformat(),
            "id": message_id,
        }
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("ascii")

    @staticmethod
    def _decode_cursor(cursor: str) -> tuple[datetime, ObjectId]:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
        payload = json.loads(raw.decode("utf-8"))
        created_at = datetime.fromisoformat(payload["created_at"])
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        message_id = ObjectId(payload["id"])
        return created_at, message_id
