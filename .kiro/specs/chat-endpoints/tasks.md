# Implementation Plan: Chat Endpoints

## Overview

Implement 2 GET endpoints cho list conversations và get messages. Follow existing patterns trong codebase với FastAPI, Pydantic schemas, và MongoDB repository.

## Tasks

- [x] 1. Add response schemas
  - [x] 1.1 Add ConversationResponse, ConversationListResponse, MessageResponse, MessageListResponse to `app/domain/schemas/chat.py`
    - Import required types from models
    - Follow existing schema patterns in the file
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [-] 2. Add repository search method
  - [x] 2.1 Add SearchResult model and search_by_user method to `app/repo/conversation_repo.py`
    - Add SearchResult Pydantic model with items and total fields
    - Implement search_by_user with status filter, title regex search, pagination
    - Use re.escape() for safe regex
    - Return both items and total count
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  - [ ]* 2.2 Write property test for search_by_user
    - **Property 4: Title Search Case-Insensitivity**
    - **Property 6: Soft-Delete Exclusion**
    - **Validates: Requirements 1.5, 1.8, 4.2, 4.4**

- [ ] 3. Add service layer methods
  - [ ] 3.1 Add search_user_conversations method to `app/services/ai/conversation_service.py`
    - Delegate to conversation_repo.search_by_user
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 1.6_
  - [ ] 3.2 Add search_conversations method to `app/services/ai/chat_service.py`
    - Delegate to conversation_service.search_user_conversations
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 1.6_

- [ ] 4. Implement list conversations endpoint
  - [ ] 4.1 Add GET /conversations endpoint to `app/api/v1/ai/chat.py`
    - Add Query parameters: skip (default 0, ge=0), limit (default 20, ge=1, le=100), status (optional), search (optional, max_length=100)
    - Call chat_service.search_conversations
    - Map Conversation models to ConversationResponse
    - Return ConversationListResponse
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_
  - [ ]* 4.2 Write property tests for list conversations
    - **Property 1: Conversation List Sorting**
    - **Property 2: Pagination Correctness**
    - **Property 3: Status Filter Accuracy**
    - **Property 5: User Isolation**
    - **Validates: Requirements 1.1, 1.2, 1.4, 1.6, 1.7**

- [ ] 5. Implement get messages endpoint
  - [ ] 5.1 Add GET /conversations/{conversation_id}/messages endpoint to `app/api/v1/ai/chat.py`
    - Verify conversation exists and user owns it (return 404 if not)
    - Get all messages via conversation_service.get_messages (no pagination needed)
    - Map Message models to MessageResponse
    - Return MessageListResponse with conversation_id
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  - [ ]* 5.2 Write property tests for get messages
    - **Property 7: Message Ordering**
    - **Property 8: Message Response Completeness**
    - **Validates: Requirements 2.1, 2.4, 2.5**

- [ ] 6. Checkpoint - Verify implementation
  - Ensure all tests pass, ask the user if questions arise.
  - Run `pytest tests/` to verify no regressions

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Follow existing code patterns in the codebase
- Use existing dependencies: get_current_active_user, get_chat_service
- Property tests use `hypothesis` library with minimum 100 iterations
