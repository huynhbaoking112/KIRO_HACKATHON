"""Service factory functions with singleton pattern."""

from functools import lru_cache

from app.common.repo import get_user_repo
from app.services.auth.auth_service import AuthService


@lru_cache
def get_auth_service() -> AuthService:
    """Get singleton AuthService instance.

    Returns:
        AuthService instance with UserRepository
    """
    user_repo = get_user_repo()
    return AuthService(user_repo)
