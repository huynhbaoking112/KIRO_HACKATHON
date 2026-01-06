"""Shared dependencies for API endpoints."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.common.exceptions import InvalidTokenError
from app.common.repo import get_user_repo
from app.common.service import get_auth_service
from app.domain.models.user import User, UserRole
from app.repo.user_repo import UserRepository
from app.services.auth.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    """Get current user from JWT token.

    Args:
        token: JWT token from Authorization header
        auth_service: AuthService dependency
        user_repo: UserRepository dependency

    Returns:
        User instance

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = auth_service.verify_token(token)
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user = await user_repo.find_by_id(payload.sub)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        User instance if active

    Raises:
        HTTPException: 401 if user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Require admin role for endpoint access.

    Args:
        current_user: User from get_current_active_user dependency

    Returns:
        User instance if admin

    Raises:
        HTTPException: 403 if user is not admin
    """
    user_role = current_user.role
    if isinstance(user_role, str):
        is_admin = user_role == UserRole.ADMIN.value
    else:
        is_admin = user_role == UserRole.ADMIN

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )
    return current_user
