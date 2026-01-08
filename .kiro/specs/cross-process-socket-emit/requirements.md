# Requirements Document

## Introduction

Tính năng Cross-Process Socket Emit cho phép các background worker processes (như Sheet Sync Worker) emit WebSocket events đến clients đang kết nối với FastAPI server. Hiện tại, worker process và FastAPI server chạy trên 2 processes riêng biệt, mỗi process có Socket.IO instance riêng, dẫn đến việc worker không thể emit events đến clients.

Giải pháp sử dụng python-socketio's AsyncRedisManager để đồng bộ events giữa các processes thông qua Redis Pub/Sub.

## Glossary

- **Socket_Gateway**: Module wrapper cho python-socketio, cung cấp API để emit events đến clients
- **AsyncRedisManager**: Client manager của python-socketio sử dụng Redis Pub/Sub để đồng bộ events giữa multiple processes
- **Write_Only_Manager**: AsyncRedisManager mode chỉ cho phép emit events, không nhận connections (dùng cho worker processes)
- **FastAPI_Server**: Main application server nơi clients kết nối WebSocket
- **Worker_Process**: Background process xử lý async tasks (Sheet Sync Worker, etc.)
- **Redis_Pub_Sub**: Redis publish/subscribe mechanism để broadcast messages giữa processes

## Requirements

### Requirement 1: Redis-backed Socket.IO Server

**User Story:** As a system operator, I want the Socket.IO server to use Redis as message queue backend, so that events can be synchronized across multiple processes.

#### Acceptance Criteria

1. WHEN the FastAPI server starts, THE Socket_Gateway SHALL initialize AsyncRedisManager with the configured Redis URL
2. WHEN the AsyncRedisManager is initialized, THE Socket_Gateway SHALL pass it as client_manager to AsyncServer
3. WHEN Redis connection fails during startup, THE System SHALL log an error and continue with local-only mode
4. THE System SHALL use the existing REDIS_URL configuration from settings

### Requirement 2: Write-Only Manager for Workers

**User Story:** As a developer, I want worker processes to emit socket events without accepting connections, so that workers can notify users about task progress.

#### Acceptance Criteria

1. WHEN a worker process needs to emit events, THE System SHALL provide a write-only AsyncRedisManager instance
2. THE Write_Only_Manager SHALL NOT accept client connections
3. THE Write_Only_Manager SHALL use the same Redis URL as the main server
4. WHEN the worker emits an event, THE event SHALL be published to Redis and received by the main server

### Requirement 3: Unified Gateway Interface

**User Story:** As a developer, I want a consistent API for emitting socket events regardless of which process I'm in, so that I don't need to change service code.

#### Acceptance Criteria

1. THE Socket_Gateway class SHALL maintain the same public interface (emit_to_user, emit_to_room, broadcast)
2. WHEN called from FastAPI server, THE Socket_Gateway SHALL emit directly via AsyncServer
3. WHEN called from worker process, THE Socket_Gateway SHALL emit via Write_Only_Manager
4. THE System SHALL provide a factory function to get the appropriate gateway instance based on context

### Requirement 4: Worker Gateway Initialization

**User Story:** As a developer, I want worker processes to easily initialize the socket gateway, so that I can emit events with minimal setup.

#### Acceptance Criteria

1. THE System SHALL provide a dedicated worker gateway module or factory function
2. WHEN a worker imports the worker gateway, THE System SHALL lazily initialize the Write_Only_Manager
3. THE Worker_Gateway SHALL NOT require the full Socket.IO server to be running
4. WHEN Redis is not available, THE Worker_Gateway SHALL log a warning and skip emit operations gracefully

### Requirement 5: Backward Compatibility

**User Story:** As a developer, I want existing code that uses the gateway to continue working without changes, so that migration is seamless.

#### Acceptance Criteria

1. THE existing `gateway` singleton import SHALL continue to work in FastAPI server context
2. THE existing emit method signatures SHALL remain unchanged
3. WHEN the system runs in single-process mode (development), THE System SHALL work without Redis manager
4. THE System SHALL support gradual migration of worker code to use the new worker gateway

### Requirement 6: Configuration

**User Story:** As a system operator, I want to configure the Redis-backed socket gateway via environment variables, so that I can customize behavior per environment.

#### Acceptance Criteria

1. THE System SHALL use the existing REDIS_URL setting for AsyncRedisManager
2. THE System MAY add an optional SOCKET_REDIS_CHANNEL setting for custom channel prefix
3. WHEN REDIS_URL is not configured, THE System SHALL fall back to local-only mode with a warning

### Requirement 7: Error Handling and Resilience

**User Story:** As a system operator, I want the socket gateway to handle Redis failures gracefully, so that the system remains stable.

#### Acceptance Criteria

1. WHEN Redis connection is lost during emit, THE System SHALL log the error and not crash
2. WHEN Redis reconnects, THE System SHALL automatically resume normal operation
3. THE System SHALL NOT block the main application flow if socket emit fails
4. WHEN emit fails in worker, THE Worker SHALL continue processing other tasks

