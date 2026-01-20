"""Group membership models for admin-managed group chats."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GroupMember(BaseModel):
    """Group member domain model representing user membership in a group."""

    id: str = Field(alias="_id")
    group_id: str
    user_id: str
    joined_at: datetime
    removed_at: Optional[datetime] = None
    added_by_admin_id: Optional[str] = None
    removed_by_admin_id: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
