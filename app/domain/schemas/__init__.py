"""Domain schemas for request/response validation."""

from app.domain.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenPayload,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.domain.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
)
from app.domain.schemas.message import (
    MessageCreate,
    MessageUpdate,
)

__all__ = [
    # Auth schemas
    "LoginRequest",
    "RegisterRequest",
    "TokenPayload",
    "TokenResponse",
    "UserCreate",
    "UserResponse",
    # Conversation schemas
    "ConversationCreate",
    "ConversationUpdate",
    # Message schemas
    "MessageCreate",
    "MessageUpdate",
]
