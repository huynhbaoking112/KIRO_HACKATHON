# Implementation Plan: Conversation Storage

## Overview

Implement hệ thống lưu trữ conversations và messages cho AI chat với MongoDB. Bao gồm Pydantic models, repository layer, service layer, và LangChain compatibility.

## Tasks

- [x] 1. Implement Pydantic Models
  - [x] 1.1 Create base models và enums trong `app/domain/models/conversation.py`
    - Implement ConversationStatus enum (active, archived)
    - Implement Conversation model với tất cả fields
    - Implement ConversationCreate, ConversationUpdate schemas
    - _Requirements: 6.1, 6.5_
  - [x] 1.2 Create message models trong `app/domain/models/message.py`
    - Implement MessageRole enum (user, assistant, system, tool)
    - Implement AttachmentType enum (image, file)
    - Implement Attachment, TokenUsage, ToolCall, MessageMetadata models
    - Implement Message model với tất cả fields
    - Implement MessageCreate, MessageUpdate schemas
    - _Requirements: 6.2, 6.3, 6.4, 6.6_
  - [ ]* 1.3 Write property tests for model validation
    - **Property 7: Attachment Type Validation**
    - **Property 8: Role Validation**
    - **Property 10: Model Validation Completeness**
    - **Validates: Requirements 3.3, 5.1, 6.1-6.6**

- [-] 2. Implement Conversation Repository
  - [x] 2.1 Create `app/repo/conversation_repo.py`
    - Implement create() method
    - Implement get_by_id() method với soft delete filter
    - Implement get_by_user() method với pagination và ordering
    - Implement update() method
    - Implement soft_delete() method
    - Implement increment_message_count() method
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_
  - [ ]* 2.2 Write property tests for ConversationRepository
    - **Property 1: Soft Delete Preserves Records** (conversation)
    - **Property 2: Soft Deleted Records Exclusion** (conversation)
    - **Property 4: Conversation Ordering**
    - **Validates: Requirements 1.2, 1.4, 1.5, 1.6**

- [ ] 3. Implement Message Repository
  - [ ] 3.1 Create `app/repo/message_repo.py`
    - Implement create() method với attachments support
    - Implement get_by_conversation() method với ordering
    - Implement update() method cho streaming support
    - Implement soft_delete() method
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2_
  - [ ]* 3.2 Write property tests for MessageRepository
    - **Property 1: Soft Delete Preserves Records** (message)
    - **Property 2: Soft Deleted Records Exclusion** (message)
    - **Property 5: Message Chronological Order**
    - **Validates: Requirements 2.2, 2.3**

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement Conversation Service
  - [ ] 5.1 Create `app/services/ai/conversation_service.py`
    - Implement create_conversation() với auto title generation
    - Implement add_message() với conversation stats update
    - Implement get_messages()
    - Implement get_langchain_messages() cho LangChain compatibility
    - Implement delete_conversation()
    - _Requirements: 2.6, 4.1, 4.2, 5.4_
  - [ ]* 5.2 Write property tests for ConversationService
    - **Property 3: Message Creation Updates Conversation Stats**
    - **Property 6: Auto Title Generation**
    - **Property 9: LangChain Message Conversion Round-Trip**
    - **Validates: Requirements 2.6, 4.1, 4.2, 5.4**

- [ ] 6. Create MongoDB Indexes
  - [ ] 6.1 Create index setup script hoặc startup hook
    - Create index cho conversations: { "user_id": 1, "deleted_at": 1, "updated_at": -1 }
    - Create index cho messages: { "conversation_id": 1, "deleted_at": 1, "created_at": 1 }
    - _Requirements: 1.2, 1.6, 2.2_

- [ ] 7. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Sử dụng Hypothesis library cho property-based testing
- Sử dụng pytest-asyncio cho async tests
- Có thể dùng mongomock hoặc testcontainers cho database tests
