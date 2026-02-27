"""Authentication routes for login and password management."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_active_user
from app.common.service import get_auth_service
from app.domain.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    TokenResponse,
)
from app.domain.models.user import User
from app.services.auth.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Login and receive JWT access token."""
    return await auth_service.authenticate_user(
        email=request.email,
        password=request.password,
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Change password for current authenticated user."""
    await auth_service.change_password(
        user_id=current_user.id,
        current_password=request.current_password,
        new_password=request.new_password,
    )
    return {"message": "Password changed successfully"}
