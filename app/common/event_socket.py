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
