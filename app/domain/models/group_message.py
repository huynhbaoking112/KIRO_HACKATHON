"""Group message model for admin-managed group chats."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GroupMessage(BaseModel):
    """Group message domain model."""

    id: str = Field(alias="_id")
    group_id: str
    sender_id: str
    content: str
    client_msg_id: Optional[str] = None
    created_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
