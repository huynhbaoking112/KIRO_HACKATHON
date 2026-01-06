"""Authentication routes for user registration and login."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.common.service import get_auth_service
from app.common.exceptions import (
    AuthenticationError,
    EmailAlreadyExistsError,
    InactiveUserError,
)
from app.domain.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Register a new user with email and password.

    Args:
        request: RegisterRequest with email and password
        auth_service: AuthService dependency

    Returns:
        UserResponse with created user information

    Raises:
        HTTPException: 400 if email already registered
    """
    try:
        user = await auth_service.register_user(
            email=request.email,
            password=request.password,
        )
    except EmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e

    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role if isinstance(user.role, str) else user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Login and receive JWT access token.

    Args:
        request: LoginRequest with email and password
        auth_service: AuthService dependency

    Returns:
        TokenResponse with access token

    Raises:
        HTTPException: 401 if credentials invalid or account inactive
    """
    try:
        token_response = await auth_service.authenticate_user(
            email=request.email,
            password=request.password,
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except InactiveUserError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    return token_response
