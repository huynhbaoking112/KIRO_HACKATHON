# Requirements Document

## Introduction

Socket Gateway là một infrastructure module cho phép server push messages real-time đến clients thông qua Socket.IO. Module này cung cấp foundation để các tính năng khác trong hệ thống có thể emit events đến users mà không cần implement socket logic riêng.

## Glossary

- **Socket_Gateway**: Module quản lý Socket.IO server và cung cấp API để emit events
- **Client**: Ứng dụng frontend (web/mobile) kết nối đến Socket Gateway
- **Room**: Logical grouping của Socket.IO để gửi messages đến nhóm connections
- **SID**: Socket session ID, unique identifier cho mỗi connection
- **JWT**: JSON Web Token dùng để authenticate client connections

## Requirements

### Requirement 1: Client Connection với JWT Authentication

**User Story:** As a client application, I want to connect to the Socket Gateway with JWT authentication, so that only authenticated users can receive real-time messages.

#### Acceptance Criteria

1. WHEN a client connects with a valid JWT token in auth object, THE Socket_Gateway SHALL accept the connection and join the client to their personal room
2. WHEN a client connects without a token, THE Socket_Gateway SHALL reject the connection with "Unauthorized" error
3. WHEN a client connects with an invalid or expired JWT token, THE Socket_Gateway SHALL reject the connection with "Unauthorized" error
4. WHEN a client successfully connects, THE Socket_Gateway SHALL automatically join the client to room "user:{user_id}"

### Requirement 2: Server Emit to User

**User Story:** As a backend service, I want to emit events to specific users, so that I can send real-time notifications and updates.

#### Acceptance Criteria

1. WHEN emit_to_user is called with user_id, event name, and data, THE Socket_Gateway SHALL emit the event to room "user:{user_id}"
2. WHEN emit_to_user is called for a user with no active connections, THE Socket_Gateway SHALL complete without error

### Requirement 3: Server Emit to Room

**User Story:** As a backend service, I want to emit events to rooms, so that I can send messages to groups of users.

#### Acceptance Criteria

1. WHEN emit_to_room is called with room name, event name, and data, THE Socket_Gateway SHALL emit the event to all clients in that room
2. WHEN emit_to_room is called for an empty room, THE Socket_Gateway SHALL complete without error

### Requirement 4: Server Broadcast

**User Story:** As a backend service, I want to broadcast events to all connected clients, so that I can send system-wide announcements.

#### Acceptance Criteria

1. WHEN broadcast is called with event name and data, THE Socket_Gateway SHALL emit the event to all connected clients

### Requirement 5: Room Management

**User Story:** As a backend service, I want to manage room membership, so that I can group users for targeted messaging.

#### Acceptance Criteria

1. WHEN join_room is called with sid and room name, THE Socket_Gateway SHALL add the connection to the specified room
2. WHEN leave_room is called with sid and room name, THE Socket_Gateway SHALL remove the connection from the specified room

### Requirement 6: FastAPI Integration

**User Story:** As a developer, I want the Socket Gateway integrated with FastAPI, so that both REST API and WebSocket run on the same server.

#### Acceptance Criteria

1. THE Socket_Gateway SHALL be mountable as an ASGI application alongside FastAPI
2. WHEN the server starts, THE Socket_Gateway SHALL be available at the root path for WebSocket connections
3. THE FastAPI REST endpoints SHALL continue to work normally after Socket_Gateway integration

### Requirement 7: Client Disconnection

**User Story:** As a system, I want to handle client disconnections gracefully, so that resources are cleaned up properly.

#### Acceptance Criteria

1. WHEN a client disconnects, THE Socket_Gateway SHALL automatically remove the client from all rooms
