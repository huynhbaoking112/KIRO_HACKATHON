# Implementation Plan: Socket Gateway

## Overview

Implement Socket Gateway module sử dụng python-socketio để cung cấp real-time server-to-client messaging với JWT authentication. Module được integrate với FastAPI thông qua ASGI.

## Tasks

- [x] 1. Setup dependencies và project structure
  - Thêm `python-socketio` vào requirements.txt
  - Tạo folder `app/socket_gateway/`
  - Tạo file `__init__.py` trống
  - _Requirements: 6.1_

- [-] 2. Implement authentication module
  - [x] 2.1 Implement `auth.py` với function `authenticate()`
    - Validate JWT token từ auth dict
    - Return `{"user_id": str}` nếu valid, `None` nếu invalid
    - Handle exceptions gracefully
    - _Requirements: 1.1, 1.2, 1.3_
  - [ ]* 2.2 Write unit tests cho authenticate function
    - Test với valid token
    - Test với invalid token
    - Test với missing token
    - Test với expired token
    - _Requirements: 1.2, 1.3_

- [ ] 3. Implement Socket.IO server
  - [ ] 3.1 Implement `server.py` với AsyncServer setup
    - Create `sio` instance với async_mode='asgi'
    - Implement `connect` event handler với JWT auth
    - Auto-join user to personal room `user:{user_id}`
    - Implement `disconnect` event handler (empty)
    - _Requirements: 1.1, 1.4, 7.1_
  - [ ]* 3.2 Write property test cho authentication và room assignment
    - **Property 1: Valid Authentication Joins Correct Room**
    - **Validates: Requirements 1.1, 1.4**
  - [ ]* 3.3 Write property test cho invalid token rejection
    - **Property 2: Invalid Token Rejection**
    - **Validates: Requirements 1.2, 1.3**

- [ ] 4. Implement SocketGateway class
  - [ ] 4.1 Implement `__init__.py` với SocketGateway class
    - Import sio từ server.py
    - Create socket_app = socketio.ASGIApp(sio)
    - Implement `emit_to_user(user_id, event, data)`
    - Implement `emit_to_room(room, event, data)`
    - Implement `broadcast(event, data)`
    - Implement `join_room(sid, room)`
    - Implement `leave_room(sid, room)`
    - Create singleton `gateway` instance
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 4.1, 5.1, 5.2_
  - [ ]* 4.2 Write property test cho emit_to_user room format
    - **Property 3: Emit to User Room Format**
    - **Validates: Requirements 2.1**
  - [ ]* 4.3 Write property test cho room operations
    - **Property 4: Room Operations Parameter Passing**
    - **Validates: Requirements 3.1, 5.1, 5.2**

- [ ] 5. Integrate với FastAPI
  - [ ] 5.1 Update `main.py` để mount Socket Gateway
    - Import sio từ socket_gateway
    - Create combined_app với socketio.ASGIApp
    - Export combined_app thay vì app
    - _Requirements: 6.1, 6.2, 6.3_

- [ ] 6. Checkpoint - Verify integration
  - Ensure all tests pass
  - Verify server starts without errors
  - Ask user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
