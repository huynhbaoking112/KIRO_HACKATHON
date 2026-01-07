# Design Document: Socket Gateway

## Overview

Socket Gateway là một lightweight infrastructure module sử dụng python-socketio để cung cấp real-time communication từ server đến clients. Module được thiết kế đơn giản, chỉ hỗ trợ server-to-client messaging (one-way) với JWT authentication.

### Key Design Decisions

1. **python-socketio với ASGI mode**: Native async support, integrate trực tiếp với FastAPI
2. **Room-based messaging**: Sử dụng built-in room management của Socket.IO thay vì custom tracking
3. **Personal room pattern**: Mỗi user auto-join room `user:{user_id}` khi connect
4. **Stateless Gateway class**: Chỉ wrap Socket.IO methods, không maintain state riêng

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client                                │
│              (socket.io-client JS/Mobile)                   │
└─────────────────────┬───────────────────────────────────────┘
                      │ WebSocket + JWT Auth
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 combined_app (ASGI)                          │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  socketio.ASGIApp                                       ││
│  │  ┌─────────────────┐    ┌─────────────────────────────┐ ││
│  │  │ Socket.IO Server│    │      FastAPI App            │ ││
│  │  │ (WebSocket)     │    │      (REST API)             │ ││
│  │  └─────────────────┘    └─────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Folder Structure

```
app/
├── socket_gateway/
│   ├── __init__.py          # SocketGateway class, exports
│   ├── server.py            # AsyncServer instance, event handlers
│   └── auth.py              # JWT authentication
├── main.py                  # Mount combined_app
```

### Component: auth.py

**Purpose**: Validate JWT token từ socket connection auth object.

```python
async def authenticate(auth: dict | None) -> dict | None:
    """
    Validate JWT token from socket auth.
    
    Args:
        auth: Auth object from client connection, expected format: {"token": "jwt-string"}
    
    Returns:
        {"user_id": str} if valid, None if invalid
    """
```

**Dependencies**: 
- `app.infrastructure.security.jwt.decode_access_token`

### Component: server.py

**Purpose**: Setup Socket.IO AsyncServer và register event handlers.

```python
# Socket.IO server instance
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # Configure for production
)

@sio.event
async def connect(sid: str, environ: dict, auth: dict) -> None:
    """
    Handle client connection.
    - Authenticate JWT
    - Join personal room user:{user_id}
    - Raise ConnectionRefusedError if auth fails
    """

@sio.event  
async def disconnect(sid: str, reason: str) -> None:
    """Handle disconnection - Socket.IO auto-cleans rooms."""
```

### Component: __init__.py (SocketGateway class)

**Purpose**: Public API để emit events từ anywhere trong codebase.

```python
class SocketGateway:
    async def emit_to_user(self, user_id: str, event: str, data: dict) -> None:
        """Emit event to specific user via their personal room."""
    
    async def emit_to_room(self, room: str, event: str, data: dict) -> None:
        """Emit event to all clients in a room."""
    
    async def broadcast(self, event: str, data: dict) -> None:
        """Emit event to all connected clients."""
    
    def join_room(self, sid: str, room: str) -> None:
        """Add a connection to a room."""
    
    def leave_room(self, sid: str, room: str) -> None:
        """Remove a connection from a room."""

# Singleton instance
gateway = SocketGateway()

# ASGI app for mounting
socket_app = socketio.ASGIApp(sio)
```

### Integration: main.py

```python
import socketio
from app.socket_gateway import sio

# Existing FastAPI app
app = FastAPI(...)

# Combine FastAPI with Socket.IO
combined_app = socketio.ASGIApp(sio, other_asgi_app=app)
```

## Data Models

### Client Auth Object

```python
# Client sends this when connecting
{
    "token": "eyJhbGciOiJIUzI1NiIs..."  # JWT token
}
```

### Event Data

```python
# Generic event data structure (flexible)
{
    "type": str,      # Optional: event subtype
    "message": str,   # Optional: human readable message
    "data": dict,     # Optional: additional payload
    # ... any other fields
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Valid Authentication Joins Correct Room

*For any* valid JWT token containing user_id U, when a client connects with that token, the authenticate function shall return {"user_id": U} and the client shall be joined to room "user:{U}".

**Validates: Requirements 1.1, 1.4**

### Property 2: Invalid Token Rejection

*For any* string that is not a valid JWT token (random strings, malformed tokens, expired tokens), the authenticate function shall return None.

**Validates: Requirements 1.2, 1.3**

### Property 3: Emit to User Room Format

*For any* user_id string U, calling emit_to_user(U, event, data) shall emit to room "user:{U}" with the exact event name and data payload.

**Validates: Requirements 2.1**

### Property 4: Room Operations Parameter Passing

*For any* room name R and sid S:
- join_room(S, R) shall call sio.enter_room with exactly (S, R)
- leave_room(S, R) shall call sio.leave_room with exactly (S, R)
- emit_to_room(R, event, data) shall call sio.emit with room=R

**Validates: Requirements 3.1, 5.1, 5.2**

## Error Handling

| Scenario | Handling |
|----------|----------|
| Invalid/missing JWT | Raise `ConnectionRefusedError('Unauthorized')` |
| Expired JWT | Raise `ConnectionRefusedError('Unauthorized')` |
| Emit to offline user | Complete silently (no error) |
| Emit to empty room | Complete silently (no error) |
| JWT decode exception | Catch and return None from authenticate |

## Testing Strategy

### Unit Tests

1. **auth.py tests**:
   - Test authenticate with valid token returns user_id
   - Test authenticate with invalid token returns None
   - Test authenticate with missing token returns None
   - Test authenticate with expired token returns None

2. **SocketGateway class tests**:
   - Test emit_to_user calls sio.emit with correct room format
   - Test emit_to_room calls sio.emit with correct room
   - Test broadcast calls sio.emit without room
   - Test join_room calls sio.enter_room
   - Test leave_room calls sio.leave_room

### Integration Tests

1. **Connection flow**:
   - Test client can connect with valid JWT
   - Test client rejected with invalid JWT
   - Test client auto-joins personal room on connect

2. **Message delivery**:
   - Test emit_to_user delivers to connected client
   - Test emit_to_room delivers to room members only

### Property-Based Tests

Property-based testing sẽ được sử dụng để verify các correctness properties với nhiều inputs khác nhau.

**Testing Framework**: pytest + hypothesis (đã có trong requirements.txt)

**Test Configuration**: Minimum 100 iterations per property test
