"""Repository factory functions with singleton pattern."""

from functools import lru_cache

from app.infrastructure.database.mongodb import MongoDB
from app.repo.user_repo import UserRepository


@lru_cache
def get_user_repo() -> UserRepository:
    """Get singleton UserRepository instance.

    Returns:
        UserRepository instance with database connection
    """
    db = MongoDB.get_db()
    return UserRepository(db)
