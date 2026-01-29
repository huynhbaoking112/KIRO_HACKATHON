"""Socket event constants for WebSocket communication.

This module defines all socket event names used throughout the application
to avoid hardcoding event strings and ensure consistency.
"""


class SheetSyncEvents:
    """Socket events for sheet synchronization."""

    STARTED = "sheet:sync:started"
    COMPLETED = "sheet:sync:completed"
    FAILED = "sheet:sync:failed"
    PROGRESS = "sheet:sync:progress"


class ChatEvents:
    """Socket events for chat message streaming."""

    MESSAGE_STARTED = "chat:message:started"
    MESSAGE_TOKEN = "chat:message:token"
    MESSAGE_TOOL_START = "chat:message:tool_start"
    MESSAGE_TOOL_END = "chat:message:tool_end"
    MESSAGE_COMPLETED = "chat:message:completed"
    MESSAGE_FAILED = "chat:message:failed"


class GroupChatEvents:
    """Socket events for group chat."""

    MEMBER_ADDED = "group:member:added"
    MEMBER_REMOVED = "group:member:removed"
    MESSAGE_CREATED = "group:message:created"
