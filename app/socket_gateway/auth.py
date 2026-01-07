"""Socket Gateway JWT authentication module."""

from jose import JWTError

from app.infrastructure.security.jwt import decode_access_token


async def authenticate(auth: dict | None) -> dict | None:
    """Validate JWT token from socket auth object.

    Args:
        auth: Auth object from client connection, expected format: {"token": "jwt-string"}

    Returns:
        {"user_id": str} if valid, None if invalid/missing/expired
    """
    if auth is None:
        return None

    token = auth.get("token")
    if not token:
        return None

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        return {"user_id": user_id}
    except JWTError:
        return None
