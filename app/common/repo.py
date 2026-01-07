"""Repository factory functions with singleton pattern."""

from functools import lru_cache

from app.infrastructure.database.mongodb import MongoDB
from app.repo.user_repo import UserRepository
from app.repo.sheet_connection_repo import SheetConnectionRepository
from app.repo.sheet_sync_state_repo import SheetSyncStateRepository
from app.repo.sheet_data_repo import SheetDataRepository


@lru_cache
def get_user_repo() -> UserRepository:
    """Get singleton UserRepository instance.

    Returns:
        UserRepository instance with database connection
    """
    db = MongoDB.get_db()
    return UserRepository(db)


@lru_cache
def get_sheet_connection_repo() -> SheetConnectionRepository:
    """Get singleton SheetConnectionRepository instance.

    Returns:
        SheetConnectionRepository instance with database connection
    """
    db = MongoDB.get_db()
    return SheetConnectionRepository(db)


@lru_cache
def get_sheet_sync_state_repo() -> SheetSyncStateRepository:
    """Get singleton SheetSyncStateRepository instance.

    Returns:
        SheetSyncStateRepository instance with database connection
    """
    db = MongoDB.get_db()
    return SheetSyncStateRepository(db)


@lru_cache
def get_sheet_data_repo() -> SheetDataRepository:
    """Get singleton SheetDataRepository instance.

    Returns:
        SheetDataRepository instance with database connection
    """
    db = MongoDB.get_db()
    return SheetDataRepository(db)
