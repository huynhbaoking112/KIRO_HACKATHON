# Design Document: Cross-Process Socket Emit

## Overview

Tính năng Cross-Process Socket Emit cho phép background worker processes emit WebSocket events đến clients thông qua Redis Pub/Sub. Sử dụng python-socketio's AsyncRedisManager để đồng bộ events giữa FastAPI server và worker processes.

### Key Design Decisions

1. **AsyncRedisManager**: Sử dụng built-in support của python-socketio cho Redis Pub/Sub
2. **Write-Only Mode**: Worker processes chỉ cần emit, không cần accept connections
3. **Lazy Initialization**: Worker gateway chỉ khởi tạo khi cần thiết
4. **Graceful Degradation**: System tiếp tục hoạt động khi Redis không available

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Server (Process 1)                       │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    Socket.IO AsyncServer                         │   │
│   │                                                                  │   │
│   │   client_manager = AsyncRedisManager(redis_url)                 │   │
│   │                                                                  │   │
│   │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │   │
│   │   │  Client 1   │    │  Client 2   │    │  Client N   │        │   │
│   │   │  (user:123) │    │  (user:456) │    │  (user:789) │        │   │
│   │   └─────────────┘    └─────────────┘    └─────────────┘        │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              ▲                                           │
│                              │ Subscribe                                 │
└──────────────────────────────┼──────────────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │       Redis         │
                    │     Pub/Sub         │
                    │                     │
                    │  Channel:           │
                    │  socketio           │
                    └──────────┬──────────┘
                               │
                               │ Publish
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Worker Process (Process 2)                          │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │              AsyncRedisManager (write_only=True)                 │   │
│   │                                                                  │   │
│   │   await manager.emit("sheet:sync:completed", data, room=room)   │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    Sheet Sync Worker                             │   │
│   │                                                                  │   │
│   │   crawler_service.sync_sheet() → emit events                    │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Socket Gateway Module Structure

```
app/socket_gateway/
├── __init__.py          # Public exports (gateway, socket_app)
├── server.py            # AsyncServer with AsyncRedisManager
├── auth.py              # Authentication (unchanged)
├── manager.py           # NEW: Redis manager factory
└── worker_gateway.py    # NEW: Write-only gateway for workers
```

### 2. Redis Manager Factory (`app/socket_gateway/manager.py`)

```python
"""Redis manager factory for Socket.IO cross-process communication."""

import logging
from typing import Optional

import socketio

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_server_manager: Optional[socketio.AsyncRedisManager] = None
_worker_manager: Optional[socketio.AsyncRedisManager] = None


def get_server_manager() -> Optional[socketio.AsyncRedisManager]:
    """Get AsyncRedisManager for the main server.
    
    Returns:
        AsyncRedisManager instance or None if Redis not configured
    """
    global _server_manager
    
    if _server_manager is not None:
        return _server_manager
    
    settings = get_settings()
    redis_url = getattr(settings, 'REDIS_URL', None)
    
    if not redis_url:
        logger.warning("REDIS_URL not configured, using local-only mode")
        return None
    
    try:
        _server_manager = socketio.AsyncRedisManager(redis_url)
        logger.info("Initialized AsyncRedisManager for server")
        return _server_manager
    except Exception as e:
        logger.error(f"Failed to initialize AsyncRedisManager: {e}")
        return None


def get_worker_manager() -> Optional[socketio.AsyncRedisManager]:
    """Get write-only AsyncRedisManager for worker processes.
    
    Returns:
        AsyncRedisManager instance (write_only=True) or None if Redis not configured
    """
    global _worker_manager
    
    if _worker_manager is not None:
        return _worker_manager
    
    settings = get_settings()
    redis_url = getattr(settings, 'REDIS_URL', None)
    
    if not redis_url:
        logger.warning("REDIS_URL not configured, worker emit will be skipped")
        return None
    
    try:
        _worker_manager = socketio.AsyncRedisManager(
            redis_url, 
            write_only=True
        )
        logger.info("Initialized write-only AsyncRedisManager for worker")
        return _worker_manager
    except Exception as e:
        logger.error(f"Failed to initialize worker AsyncRedisManager: {e}")
        return None
```

### 3. Updated Server (`app/socket_gateway/server.py`)

```python
"""Socket.IO AsyncServer setup and event handlers."""

import socketio

from app.socket_gateway.auth import authenticate
from app.socket_gateway.manager import get_server_manager

# Get Redis manager (may be None if Redis not configured)
client_manager = get_server_manager()

# Socket.IO server instance with optional Redis manager
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    client_manager=client_manager,  # None = local-only mode
)


@sio.event
async def connect(sid: str, environ: dict, auth: dict | None = None) -> None:
    """Handle client connection."""
    user_data = await authenticate(auth, environ)
    if user_data is None:
        raise ConnectionRefusedError("Unauthorized")
    
    user_id = user_data["user_id"]
    await sio.enter_room(sid, f"user:{user_id}")


@sio.event
async def disconnect(sid: str) -> None:
    """Handle client disconnection."""
    pass
```

### 4. Worker Gateway (`app/socket_gateway/worker_gateway.py`)

```python
"""Write-only Socket Gateway for worker processes.

This module provides a gateway that emits events via Redis Pub/Sub
without requiring a full Socket.IO server.
"""

import logging
from typing import Optional

from app.socket_gateway.manager import get_worker_manager

logger = logging.getLogger(__name__)


class WorkerSocketGateway:
    """Socket gateway for worker processes using write-only Redis manager."""
    
    def __init__(self):
        """Initialize WorkerSocketGateway with lazy manager initialization."""
        self._manager = None
        self._initialized = False
    
    @property
    def manager(self):
        """Lazily initialize the Redis manager."""
        if not self._initialized:
            self._manager = get_worker_manager()
            self._initialized = True
        return self._manager
    
    async def emit_to_user(self, user_id: str, event: str, data: dict) -> None:
        """Emit event to a specific user via their personal room.
        
        Args:
            user_id: The user's ID
            event: Event name
            data: Event payload data
        """
        if self.manager is None:
            logger.warning(f"Cannot emit {event}: Redis manager not available")
            return
        
        room = f"user:{user_id}"
        try:
            await self.manager.emit(event, data, room=room)
        except Exception as e:
            logger.error(f"Failed to emit {event} to user {user_id}: {e}")
    
    async def emit_to_room(self, room: str, event: str, data: dict) -> None:
        """Emit event to all clients in a room.
        
        Args:
            room: Room name
            event: Event name
            data: Event payload data
        """
        if self.manager is None:
            logger.warning(f"Cannot emit {event}: Redis manager not available")
            return
        
        try:
            await self.manager.emit(event, data, room=room)
        except Exception as e:
            logger.error(f"Failed to emit {event} to room {room}: {e}")
    
    async def broadcast(self, event: str, data: dict) -> None:
        """Emit event to all connected clients.
        
        Args:
            event: Event name
            data: Event payload data
        """
        if self.manager is None:
            logger.warning(f"Cannot broadcast {event}: Redis manager not available")
            return
        
        try:
            await self.manager.emit(event, data)
        except Exception as e:
            logger.error(f"Failed to broadcast {event}: {e}")


# Singleton instance for worker processes
worker_gateway = WorkerSocketGateway()
```

### 5. Updated Main Gateway (`app/socket_gateway/__init__.py`)

```python
"""Socket Gateway module for real-time server-to-client messaging.

This module provides:
- SocketGateway: For use in FastAPI server context
- WorkerSocketGateway: For use in worker processes (via worker_gateway)
"""

import socketio

from app.socket_gateway.server import sio

# ASGI app for mounting with FastAPI
socket_app = socketio.ASGIApp(sio)


class SocketGateway:
    """Public API for emitting events to clients.
    
    This class provides methods to emit events to specific users,
    rooms, or broadcast to all connected clients.
    
    Use this in FastAPI server context. For worker processes,
    use worker_gateway from app.socket_gateway.worker_gateway.
    """

    async def emit_to_user(self, user_id: str, event: str, data: dict) -> None:
        """Emit event to a specific user via their personal room."""
        room = f"user:{user_id}"
        await sio.emit(event, data, room=room)

    async def emit_to_room(self, room: str, event: str, data: dict) -> None:
        """Emit event to all clients in a room."""
        await sio.emit(event, data, room=room)

    async def broadcast(self, event: str, data: dict) -> None:
        """Emit event to all connected clients."""
        await sio.emit(event, data)

    async def join_room(self, sid: str, room: str) -> None:
        """Add a connection to a room."""
        await sio.enter_room(sid, room)

    async def leave_room(self, sid: str, room: str) -> None:
        """Remove a connection from a room."""
        await sio.leave_room(sid, room)


# Singleton instance for FastAPI server context
gateway = SocketGateway()

# Re-export worker gateway for convenience
from app.socket_gateway.worker_gateway import worker_gateway

__all__ = ['gateway', 'worker_gateway', 'socket_app', 'SocketGateway']
```

## Data Models

Không có data models mới. Feature này chỉ modify infrastructure layer.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Cross-Process Event Delivery

*For any* event emitted by a worker process via WorkerSocketGateway, if Redis is available and a client is connected to the room, the client should receive the event.

**Validates: Requirements 2.4**

### Property 2: Graceful Error Handling

*For any* emit operation that fails (due to Redis unavailability or other errors), the calling code should not raise an exception and should continue execution normally.

**Validates: Requirements 7.1, 7.3**

### Property 3: Interface Compatibility

*For any* method call on WorkerSocketGateway, the method signature (name, parameters) should match the corresponding method on SocketGateway.

**Validates: Requirements 3.1, 5.2**

## Error Handling

### Initialization Errors

| Error | Handling |
|-------|----------|
| Redis URL not configured | Log warning, use local-only mode |
| Redis connection failed | Log error, return None manager |
| Invalid Redis URL format | Log error, return None manager |

### Runtime Errors

| Error | Handling |
|-------|----------|
| Redis connection lost during emit | Log error, skip emit, continue |
| Invalid event data | Log error, skip emit, continue |
| Room not found | Silent skip (normal behavior) |

### Worker-Specific Errors

| Error | Handling |
|-------|----------|
| Manager not initialized | Log warning, skip emit |
| Emit timeout | Log error, skip emit, continue task |

## Testing Strategy

### Unit Tests

Unit tests verify specific examples and edge cases:

- Manager factory returns correct instance types
- Server manager has write_only=False
- Worker manager has write_only=True
- Gateway methods have correct signatures
- Error handling logs correctly and doesn't raise

### Property-Based Tests

Property-based tests verify universal properties using `hypothesis`:

- **Property 1**: Cross-process delivery (requires integration test with Redis)
- **Property 2**: Error handling never raises exceptions
- **Property 3**: Interface compatibility between gateways

### Integration Tests

- Worker emits event → Server receives → Client receives
- Redis disconnect → Emit fails gracefully → Redis reconnect → Emit works
- Multiple workers emit simultaneously → All events delivered

### Test Configuration

```python
# pytest configuration
import pytest

@pytest.fixture
def redis_url():
    return "redis://localhost:6379/1"  # Use separate DB for tests

@pytest.fixture
async def server_manager(redis_url):
    import socketio
    return socketio.AsyncRedisManager(redis_url)

@pytest.fixture
async def worker_manager(redis_url):
    import socketio
    return socketio.AsyncRedisManager(redis_url, write_only=True)
```

## Configuration

### Environment Variables

```python
# app/config/settings.py (existing)
REDIS_URL: str = "redis://localhost:6379"  # Already exists

# Optional new setting (if needed for channel customization)
# SOCKET_REDIS_CHANNEL: str = "socketio"  # Default channel prefix
```

### Dependencies

```
# requirements.txt (already present)
python-socketio[asyncio_client]
redis
```

## Migration Guide

### For Worker Code

**Before:**
```python
# app/services/business/sheet_crawler/crawler_service.py
from app.socket_gateway import gateway

# This doesn't work in worker process!
await gateway.emit_to_user(user_id, event, data)
```

**After:**
```python
# app/services/business/sheet_crawler/crawler_service.py
from app.socket_gateway.worker_gateway import worker_gateway

# This works in worker process via Redis Pub/Sub
await worker_gateway.emit_to_user(user_id, event, data)
```

### For FastAPI Server Code

No changes required. The existing `gateway` singleton continues to work.

## Folder Structure Changes

```
app/socket_gateway/
├── __init__.py          # Updated: re-export worker_gateway
├── server.py            # Updated: use AsyncRedisManager
├── auth.py              # Unchanged
├── manager.py           # NEW: Redis manager factory
└── worker_gateway.py    # NEW: Write-only gateway for workers
```
