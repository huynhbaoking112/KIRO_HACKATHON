# Requirements Document

## Introduction

Feature này implement 2 REST endpoints để list conversations và get messages của một conversation trong AI chat backend service. Endpoints cho phép users xem lịch sử chat với pagination, filtering, và search capabilities.

## Glossary

- **Chat_API**: FastAPI router xử lý các chat-related endpoints
- **Conversation_Repository**: Data access layer cho conversation operations
- **Conversation_Service**: Business logic layer cho conversation management
- **User**: Authenticated user từ JWT token
- **Pagination**: Cơ chế skip/limit để phân trang kết quả
- **Soft_Delete**: Pattern đánh dấu deleted_at thay vì xóa record

## Requirements

### Requirement 1: List User Conversations

**User Story:** As a user, I want to list my conversations with pagination and filtering, so that I can browse and find my chat history efficiently.

#### Acceptance Criteria

1. WHEN a user requests their conversations THEN the Chat_API SHALL return a paginated list sorted by updated_at descending
2. WHEN a user provides skip and limit parameters THEN the Chat_API SHALL apply pagination with default skip=0, limit=20, and maximum limit=100
3. WHEN a user provides an invalid limit (greater than 100) THEN the Chat_API SHALL cap the limit at 100
4. WHEN a user provides a status filter THEN the Chat_API SHALL return only conversations matching that status (active/archived)
5. WHEN a user provides a title search query THEN the Chat_API SHALL return conversations with titles matching case-insensitively using partial match
6. THE Chat_API SHALL return total count of matching conversations for pagination UI
7. THE Chat_API SHALL only return conversations owned by the authenticated user
8. THE Chat_API SHALL exclude soft-deleted conversations from results

### Requirement 2: Get Conversation Messages

**User Story:** As a user, I want to retrieve all messages from a specific conversation, so that I can view the complete chat history with full details.

#### Acceptance Criteria

1. WHEN a user requests messages for a conversation they own THEN the Chat_API SHALL return all messages sorted by created_at ascending
2. WHEN a user requests messages for a conversation they do not own THEN the Chat_API SHALL return 404 Not Found
3. WHEN a user requests messages for a non-existent conversation THEN the Chat_API SHALL return 404 Not Found
4. THE Chat_API SHALL return full message metadata including model, tokens, latency, and tool_calls
5. THE Chat_API SHALL return complete attachment information for each message
6. THE Chat_API SHALL include the conversation_id in the response

### Requirement 3: Response Schemas

**User Story:** As a developer, I want well-defined response schemas, so that API consumers have clear contracts for integration.

#### Acceptance Criteria

1. THE ConversationResponse schema SHALL include id, title, status, message_count, last_message_at, created_at, and updated_at fields
2. THE ConversationListResponse schema SHALL include items (list of ConversationResponse), total, skip, and limit fields
3. THE MessageResponse schema SHALL include id, role, content, attachments, metadata, is_complete, and created_at fields
4. THE MessageListResponse schema SHALL include conversation_id and messages (list of MessageResponse) fields

### Requirement 4: Repository Layer Enhancement

**User Story:** As a developer, I want a search method in the repository, so that I can efficiently query conversations with filters.

#### Acceptance Criteria

1. THE Conversation_Repository SHALL provide a search_by_user method supporting status filter, title search, and pagination
2. WHEN title search is provided THEN the Conversation_Repository SHALL use case-insensitive regex matching
3. THE search_by_user method SHALL return both the list of conversations and total count in a single query operation
4. THE search_by_user method SHALL exclude soft-deleted conversations
