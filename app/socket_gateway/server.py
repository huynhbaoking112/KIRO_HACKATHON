"""Socket.IO AsyncServer setup and event handlers."""

import socketio

from app.socket_gateway.auth import authenticate

# Socket.IO server instance
sio = socketio.AsyncServer(
    async_mode="asgi",
    # TODO 07/01/2026 Add allow orgin for verify domain
    cors_allowed_origins="*",  # Configure for production
)


@sio.event
async def connect(sid: str, environ: dict, auth: dict | None = None) -> None:
    """Handle client connection.

    Authenticates JWT token and joins user to their personal room.
    Token can be provided via:
    - auth object: {"token": "jwt-string"}
    - query params: ?token=jwt-string (for Postman testing)

    Args:
        sid: Socket session ID
        environ: WSGI environ dict
        auth: Auth object from client, expected format: {"token": "jwt-string"}

    Raises:
        ConnectionRefusedError: If authentication fails
    """
    user_data = await authenticate(auth, environ)

    if user_data is None:
        raise ConnectionRefusedError("Unauthorized")

    user_id = user_data["user_id"]
    # Auto-join user to personal room
    await sio.enter_room(sid, f"user:{user_id}")


@sio.event
async def disconnect(sid: str) -> None:
    """Handle client disconnection.

    Socket.IO automatically removes the client from all rooms on disconnect.

    Args:
        sid: Socket session ID
    """
    pass
