"""Domain models for the application."""

from app.domain.models.conversation import (
    Conversation,
    ConversationStatus,
)
from app.domain.models.message import (
    Attachment,
    AttachmentType,
    Message,
    MessageMetadata,
    MessageRole,
    TokenUsage,
    ToolCall,
)
from app.domain.models.group import Group
from app.domain.models.group_member import GroupMember
from app.domain.models.group_message import GroupMessage
from app.domain.models.sheet_connection import (
    SheetConnection,
    SheetRawData,
    SheetSyncState,
)
from app.domain.models.user import User, UserRole

__all__ = [
    # Conversation models
    "Conversation",
    "ConversationStatus",
    # Message models
    "Attachment",
    "AttachmentType",
    "Message",
    "MessageMetadata",
    "MessageRole",
    "TokenUsage",
    "ToolCall",
    # Group chat models
    "Group",
    "GroupMember",
    "GroupMessage",
    # Sheet models
    "SheetConnection",
    "SheetRawData",
    "SheetSyncState",
    # User models
    "User",
    "UserRole",
]
