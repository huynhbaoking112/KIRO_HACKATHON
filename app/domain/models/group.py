"""Group chat models for admin-managed group chats."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Group(BaseModel):
    """Group domain model representing a chat group."""

    id: str = Field(alias="_id")
    name: str
    created_by_admin_id: str
    created_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
