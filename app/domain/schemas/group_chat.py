"""Schemas for admin-managed group chat feature."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateGroupRequest(BaseModel):
    """Request schema for creating a group."""

    name: str = Field(..., min_length=1, max_length=200)


class GroupResponse(BaseModel):
    """Response schema for a group."""

    id: str
    name: str
    created_by_admin_id: str
    created_at: datetime


class GroupListResponse(BaseModel):
    """Response schema for paginated group list."""

    items: list[GroupResponse]
    total: int
    skip: int
    limit: int


class AddGroupMemberRequest(BaseModel):
    """Request schema for adding a user to a group."""

    user_id: str


class GroupMemberResponse(BaseModel):
    """Response schema for a group member."""

    group_id: str
    user_id: str
    joined_at: datetime
    removed_at: Optional[datetime] = None


class SendGroupMessageRequest(BaseModel):
    """Request schema for sending a group message."""

    content: str = Field(..., min_length=1, max_length=10000)
    client_msg_id: Optional[str] = None


class GroupMessageResponse(BaseModel):
    """Response schema for a group message."""

    id: str
    group_id: str
    sender_id: str
    content: str
    created_at: datetime


class GroupMessageListResponse(BaseModel):
    """Response schema for paginated group messages."""

    group_id: str
    items: list[GroupMessageResponse]
    next_cursor: Optional[str] = None


class GroupMemberAddedPayload(BaseModel):
    """Socket payload for group:member:added."""

    group_id: str
    added_at: datetime


class GroupMemberRemovedPayload(BaseModel):
    """Socket payload for group:member:removed."""

    group_id: str
    removed_at: datetime


class GroupMessageCreatedPayload(BaseModel):
    """Socket payload for group:message:created."""

    id: str
    group_id: str
    sender_id: str
    content: str
    created_at: datetime
