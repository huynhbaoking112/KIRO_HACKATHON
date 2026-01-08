# Implementation Plan: Cross-Process Socket Emit

## Overview

Implementation plan cho tính năng Cross-Process Socket Emit sử dụng python-socketio's AsyncRedisManager. Tasks được sắp xếp theo thứ tự: Manager Factory → Server Update → Worker Gateway → Service Migration → Testing.

## Tasks

- [x] 1. Implement Redis Manager Factory
  - [x] 1.1 Create manager.py module
    - Create `app/socket_gateway/manager.py`
    - Implement `get_server_manager()` function returning AsyncRedisManager
    - Implement `get_worker_manager()` function returning AsyncRedisManager with write_only=True
    - Add proper logging for initialization success/failure
    - Handle case when REDIS_URL is not configured (return None)
    - _Requirements: 1.1, 1.3, 2.1, 2.3, 6.1, 6.3_

- [x] 2. Update Socket.IO Server
  - [x] 2.1 Update server.py to use AsyncRedisManager
    - Import `get_server_manager` from manager module
    - Pass manager as `client_manager` parameter to AsyncServer
    - Handle None manager (local-only mode)
    - _Requirements: 1.1, 1.2, 5.3_

- [x] 3. Implement Worker Gateway
  - [x] 3.1 Create worker_gateway.py module
    - Create `app/socket_gateway/worker_gateway.py`
    - Implement `WorkerSocketGateway` class with lazy manager initialization
    - Implement `emit_to_user`, `emit_to_room`, `broadcast` methods
    - Add error handling that logs but doesn't raise exceptions
    - Create `worker_gateway` singleton instance
    - _Requirements: 2.1, 2.2, 3.1, 3.3, 4.1, 4.2, 4.3, 4.4, 7.1, 7.3_
  - [ ]* 3.2 Write unit tests for WorkerSocketGateway
    - Test lazy initialization behavior
    - Test graceful handling when Redis not available
    - Test emit methods don't raise exceptions on error
    - _Requirements: 4.2, 4.4, 7.1_

- [ ] 4. Update Main Gateway Module
  - [ ] 4.1 Update __init__.py exports
    - Update `app/socket_gateway/__init__.py`
    - Re-export `worker_gateway` from worker_gateway module
    - Update `__all__` list
    - Keep existing `gateway` singleton unchanged
    - _Requirements: 3.4, 5.1, 5.5_

- [ ] 5. Checkpoint - Core Implementation Complete
  - Verify manager factory creates correct instances
  - Verify server uses AsyncRedisManager
  - Verify worker_gateway can be imported independently
  - Ask the user if questions arise

- [ ] 6. Migrate Worker Code
  - [ ] 6.1 Update crawler_service.py to use worker_gateway
    - Update import from `gateway` to `worker_gateway`
    - Replace `gateway.emit_to_user` calls with `worker_gateway.emit_to_user`
    - _Requirements: 3.3_
  - [ ] 6.2 Update sheet_sync_worker.py to use worker_gateway
    - Update import from `gateway` to `worker_gateway`
    - Replace `gateway.emit_to_user` calls with `worker_gateway.emit_to_user`
    - _Requirements: 3.3, 7.4_

- [ ] 7. Final Checkpoint
  - Test end-to-end: Worker emit → Redis → Server → Client
  - Verify backward compatibility for FastAPI server code
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Feature requires Redis to be running for cross-process communication
- In development without Redis, system falls back to local-only mode
- Worker should be restarted after migration to pick up new gateway
