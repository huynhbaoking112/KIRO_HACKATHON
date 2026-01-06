"""Custom exceptions for the application."""


class AppException(Exception):
    """Base exception for application errors."""

    default_message: str = "An error occurred"

    def __init__(self, message: str = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class AuthenticationError(AppException):
    """Raised when authentication fails (invalid email or password)."""

    default_message = "Invalid email or password"


class InvalidTokenError(AppException):
    """Raised when JWT token is invalid or expired."""

    default_message = "Invalid token"


class EmailAlreadyExistsError(AppException):
    """Raised when email is already registered."""

    default_message = "Email already registered"


class UserNotFoundError(AppException):
    """Raised when user is not found."""

    default_message = "User not found"


class InactiveUserError(AppException):
    """Raised when user account is inactive."""

    default_message = "Account is inactive"


class PermissionDeniedError(AppException):
    """Raised when user lacks required permissions."""

    default_message = "Permission denied"
