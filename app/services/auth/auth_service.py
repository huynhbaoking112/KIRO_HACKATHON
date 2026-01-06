"""Authentication service for user registration and login."""

from jose import JWTError

from app.common.exceptions import (
    AuthenticationError,
    EmailAlreadyExistsError,
    InactiveUserError,
    InvalidTokenError,
)
from app.domain.models.user import User
from app.domain.schemas.auth import TokenPayload, TokenResponse
from app.infrastructure.security.jwt import create_access_token, decode_access_token
from app.infrastructure.security.password import hash_password, verify_password
from app.repo.user_repo import UserRepository


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self, user_repo: UserRepository):
        """Initialize AuthService with user repository.

        Args:
            user_repo: UserRepository instance for database operations
        """
        self.user_repo = user_repo

    async def register_user(self, email: str, password: str) -> User:
        """Register a new user with email and password.

        Args:
            email: User email address
            password: Plain text password (will be hashed)

        Returns:
            Created User instance

        Raises:
            EmailAlreadyExistsError: If email is already registered
        """
        existing_user = await self.user_repo.find_by_email(email)
        if existing_user is not None:
            raise EmailAlreadyExistsError()

        hashed = hash_password(password)
        user = await self.user_repo.create(email=email, hashed_password=hashed)

        return user

    async def authenticate_user(self, email: str, password: str) -> TokenResponse:
        """Authenticate user and return JWT token.

        Args:
            email: User email address
            password: Plain text password

        Returns:
            TokenResponse with access token

        Raises:
            AuthenticationError: If email not found or password incorrect
            InactiveUserError: If user account is inactive
        """
        user = await self.user_repo.find_by_email(email)

        if user is None:
            raise AuthenticationError()

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError()

        if not user.is_active:
            raise InactiveUserError()

        token = self.create_access_token(user)

        return TokenResponse(access_token=token)

    def create_access_token(self, user: User) -> str:
        """Create JWT access token for user.

        Args:
            user: User instance to create token for

        Returns:
            JWT access token string
        """
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role if isinstance(user.role, str) else user.role.value,
        }

        return create_access_token(token_data)

    def verify_token(self, token: str) -> TokenPayload:
        """Verify and decode JWT token.

        Args:
            token: JWT token string to verify

        Returns:
            TokenPayload with decoded token data

        Raises:
            InvalidTokenError: If token is invalid or expired
        """
        try:
            payload = decode_access_token(token)

            return TokenPayload(
                sub=payload["sub"],
                email=payload["email"],
                role=payload["role"],
                exp=payload["exp"],
                iat=payload["iat"],
            )
        except JWTError as e:
            error_message = str(e).lower()
            if "expired" in error_message:
                raise InvalidTokenError("Token has expired") from e
            raise InvalidTokenError() from e
