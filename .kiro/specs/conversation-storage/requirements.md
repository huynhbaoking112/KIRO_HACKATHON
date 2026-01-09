# Requirements Document

## Introduction

Hệ thống lưu trữ conversations và messages cho AI chat. Thiết kế tập trung vào việc lưu trữ dữ liệu với schema linh hoạt, hỗ trợ streaming, attachments, và tương thích với LangChain ecosystem để thuận lợi cho việc tích hợp AI sau này.

## Glossary

- **Conversation**: Một cuộc hội thoại giữa user và AI, chứa nhiều messages
- **Message**: Một tin nhắn trong conversation, có thể từ user, assistant, system hoặc tool
- **Attachment**: File đính kèm trong message (image, file)
- **Soft_Delete**: Đánh dấu deleted_at thay vì xóa hẳn khỏi database
- **Conversation_Repository**: Layer truy cập dữ liệu cho conversations collection
- **Message_Repository**: Layer truy cập dữ liệu cho messages collection
- **Conversation_Service**: Business logic layer xử lý conversations và messages

## Requirements

### Requirement 1: Conversation Management

**User Story:** As a developer, I want to manage conversations for each user, so that I can organize and track chat sessions.

#### Acceptance Criteria

1. THE Conversation_Repository SHALL create a new conversation with user_id, auto-generated title, and status "active"
2. THE Conversation_Repository SHALL retrieve conversations by user_id with pagination, excluding soft-deleted records
3. THE Conversation_Repository SHALL update conversation title, status, message_count, and last_message_at
4. WHEN a conversation is deleted, THE Conversation_Repository SHALL set deleted_at timestamp instead of removing the record
5. THE Conversation_Repository SHALL retrieve a single conversation by id, excluding soft-deleted records
6. WHEN retrieving conversations, THE Conversation_Repository SHALL order by updated_at descending by default

### Requirement 2: Message Management

**User Story:** As a developer, I want to store and retrieve messages within conversations, so that I can maintain chat history.

#### Acceptance Criteria

1. THE Message_Repository SHALL create a new message with conversation_id, role, content, and optional attachments
2. THE Message_Repository SHALL retrieve messages by conversation_id in chronological order, excluding soft-deleted records
3. WHEN a message is deleted, THE Message_Repository SHALL set deleted_at timestamp instead of removing the record
4. THE Message_Repository SHALL support storing AI metadata including model, tokens, latency_ms, finish_reason, and tool_calls
5. THE Message_Repository SHALL support streaming by allowing is_complete flag to be updated
6. WHEN a new message is added, THE Conversation_Service SHALL update conversation's message_count and last_message_at

### Requirement 3: Attachment Support

**User Story:** As a developer, I want to store message attachments metadata, so that I can support file and image uploads in chat.

#### Acceptance Criteria

1. THE Message_Repository SHALL store attachment metadata including type, url, filename, mime_type, and size_bytes
2. THE Message_Repository SHALL support multiple attachments per message
3. WHEN creating a message with attachments, THE Message_Repository SHALL validate attachment type is either "image" or "file"

### Requirement 4: Auto-generate Conversation Title

**User Story:** As a developer, I want conversation titles to be auto-generated, so that users don't need to manually name conversations.

#### Acceptance Criteria

1. WHEN a conversation is created without a title, THE Conversation_Service SHALL generate a default title
2. WHEN the first user message is added to a conversation with default title, THE Conversation_Service SHALL update title based on message content (truncated to 50 characters)

### Requirement 5: LangChain Compatibility

**User Story:** As a developer, I want the storage layer to be compatible with LangChain, so that I can easily integrate AI features later.

#### Acceptance Criteria

1. THE Message_Repository SHALL store messages with roles compatible with LangChain: "user", "assistant", "system", "tool"
2. THE Message_Repository SHALL store tool_calls array for assistant messages that invoke tools
3. THE Message_Repository SHALL store tool_call_id for tool response messages
4. THE Conversation_Service SHALL provide a method to retrieve messages in LangChain BaseMessage format

### Requirement 6: Data Models

**User Story:** As a developer, I want well-defined Pydantic models, so that I have type safety and validation.

#### Acceptance Criteria

1. THE Conversation model SHALL include fields: id, user_id, title, status, message_count, last_message_at, created_at, updated_at, deleted_at
2. THE Message model SHALL include fields: id, conversation_id, role, content, attachments, metadata, is_complete, created_at, deleted_at
3. THE Attachment model SHALL include fields: type, url, filename, mime_type, size_bytes
4. THE MessageMetadata model SHALL include fields: model, tokens, latency_ms, finish_reason, tool_calls, tool_call_id
5. THE Conversation model SHALL validate status is either "active" or "archived"
6. THE Message model SHALL validate role is one of "user", "assistant", "system", "tool"
