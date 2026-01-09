# Design Document: Conversation Storage

## Overview

Thiết kế hệ thống lưu trữ conversations và messages cho AI chat sử dụng MongoDB. Hệ thống bao gồm:
- Pydantic models cho data validation
- Repository layer cho database operations
- Service layer cho business logic
- LangChain compatibility adapter

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Service Layer                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │           ConversationService                    │    │
│  │  - create_conversation()                         │    │
│  │  - add_message()                                 │    │
│  │  - get_langchain_messages()                      │    │
│  │  - auto_generate_title()                         │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Repository Layer                       │
│  ┌────────────────────┐    ┌────────────────────┐       │
│  │ ConversationRepo   │    │   MessageRepo      │       │
│  │ - create()         │    │ - create()         │       │
│  │ - get_by_id()      │    │ - get_by_conv_id() │       │
│  │ - get_by_user()    │    │ - update()         │       │
│  │ - update()         │    │ - soft_delete()    │       │
│  │ - soft_delete()    │    └────────────────────┘       │
│  └────────────────────┘                                  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                      MongoDB                             │
│  ┌────────────────────┐    ┌────────────────────┐       │
│  │   conversations    │    │     messages       │       │
│  └────────────────────┘    └────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Pydantic Models

#### Attachment Model
```python
class AttachmentType(str, Enum):
    IMAGE = "image"
    FILE = "file"

class Attachment(BaseModel):
    type: AttachmentType
    url: str
    filename: str
    mime_type: str
    size_bytes: int
```

#### Message Metadata Model
```python
class TokenUsage(BaseModel):
    prompt: int = 0
    completion: int = 0
    total: int = 0

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict

class MessageMetadata(BaseModel):
    model: str | None = None
    tokens: TokenUsage | None = None
    latency_ms: int | None = None
    finish_reason: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
```

#### Message Model
```python
class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class Message(BaseModel):
    id: PyObjectId
    conversation_id: PyObjectId
    role: MessageRole
    content: str
    attachments: list[Attachment] = []
    metadata: MessageMetadata | None = None
    is_complete: bool = True
    created_at: datetime
    deleted_at: datetime | None = None
```

#### Conversation Model
```python
class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"

class Conversation(BaseModel):
    id: PyObjectId
    user_id: PyObjectId
    title: str
    status: ConversationStatus = ConversationStatus.ACTIVE
    message_count: int = 0
    last_message_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
```

### 2. Repository Interfaces

#### ConversationRepository
```python
class ConversationRepository:
    async def create(self, user_id: ObjectId, title: str | None = None) -> Conversation
    async def get_by_id(self, conversation_id: ObjectId) -> Conversation | None
    async def get_by_user(self, user_id: ObjectId, skip: int = 0, limit: int = 20) -> list[Conversation]
    async def update(self, conversation_id: ObjectId, **fields) -> Conversation | None
    async def soft_delete(self, conversation_id: ObjectId) -> bool
    async def increment_message_count(self, conversation_id: ObjectId) -> None
```

#### MessageRepository
```python
class MessageRepository:
    async def create(self, data: MessageCreate) -> Message
    async def get_by_conversation(self, conversation_id: ObjectId) -> list[Message]
    async def update(self, message_id: ObjectId, **fields) -> Message | None
    async def soft_delete(self, message_id: ObjectId) -> bool
```

### 3. Service Interface

```python
class ConversationService:
    async def create_conversation(self, user_id: ObjectId) -> Conversation
    async def add_message(self, conversation_id: ObjectId, role: str, content: str, 
                          attachments: list[Attachment] | None = None,
                          metadata: MessageMetadata | None = None) -> Message
    async def get_messages(self, conversation_id: ObjectId) -> list[Message]
    async def get_langchain_messages(self, conversation_id: ObjectId) -> list[BaseMessage]
    async def delete_conversation(self, conversation_id: ObjectId) -> bool
```

## Data Models

### MongoDB Collections

#### conversations
```javascript
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "title": String,
  "status": "active" | "archived",
  "message_count": Int,
  "last_message_at": DateTime | null,
  "created_at": DateTime,
  "updated_at": DateTime,
  "deleted_at": DateTime | null
}

// Indexes
{ "user_id": 1, "deleted_at": 1, "updated_at": -1 }
```

#### messages
```javascript
{
  "_id": ObjectId,
  "conversation_id": ObjectId,
  "role": "user" | "assistant" | "system" | "tool",
  "content": String,
  "attachments": [{
    "type": "image" | "file",
    "url": String,
    "filename": String,
    "mime_type": String,
    "size_bytes": Int
  }],
  "metadata": {
    "model": String | null,
    "tokens": { "prompt": Int, "completion": Int, "total": Int } | null,
    "latency_ms": Int | null,
    "finish_reason": String | null,
    "tool_calls": [{ "id": String, "name": String, "arguments": Object }] | null,
    "tool_call_id": String | null
  },
  "is_complete": Boolean,
  "created_at": DateTime,
  "deleted_at": DateTime | null
}

// Indexes
{ "conversation_id": 1, "deleted_at": 1, "created_at": 1 }
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Soft Delete Preserves Records
*For any* conversation or message, when soft_delete is called, the record SHALL still exist in the database with deleted_at set to a non-null timestamp, and the original data SHALL remain unchanged.
**Validates: Requirements 1.4, 2.3**

### Property 2: Soft Deleted Records Exclusion
*For any* query operation (get_by_id, get_by_user, get_by_conversation), soft-deleted records (deleted_at != null) SHALL NOT be included in the results.
**Validates: Requirements 1.2, 1.5, 2.2**

### Property 3: Message Creation Updates Conversation Stats
*For any* message added to a conversation, the conversation's message_count SHALL increment by 1 and last_message_at SHALL be updated to the message's created_at timestamp.
**Validates: Requirements 2.6**

### Property 4: Conversation Ordering
*For any* list of conversations returned by get_by_user, the conversations SHALL be ordered by updated_at in descending order.
**Validates: Requirements 1.6**

### Property 5: Message Chronological Order
*For any* list of messages returned by get_by_conversation, the messages SHALL be ordered by created_at in ascending order.
**Validates: Requirements 2.2**

### Property 6: Auto Title Generation
*For any* conversation created without a title, a default title SHALL be assigned. When the first user message is added to a conversation with default title, the title SHALL be updated to the first 50 characters of the message content.
**Validates: Requirements 4.1, 4.2**

### Property 7: Attachment Type Validation
*For any* message with attachments, each attachment's type SHALL be either "image" or "file". Invalid types SHALL be rejected with validation error.
**Validates: Requirements 3.3**

### Property 8: Role Validation
*For any* message, the role SHALL be one of "user", "assistant", "system", "tool". Invalid roles SHALL be rejected with validation error.
**Validates: Requirements 5.1, 6.6**

### Property 9: LangChain Message Conversion Round-Trip
*For any* list of messages stored in the database, converting to LangChain BaseMessage format and back SHALL preserve the essential data (role, content, tool_calls, tool_call_id).
**Validates: Requirements 5.4**

### Property 10: Model Validation Completeness
*For any* Conversation model, it SHALL contain all required fields (id, user_id, title, status, message_count, created_at, updated_at) with correct types. *For any* Message model, it SHALL contain all required fields (id, conversation_id, role, content, is_complete, created_at) with correct types.
**Validates: Requirements 6.1, 6.2, 6.5, 6.6**

## Error Handling

| Error Case | Handling |
|------------|----------|
| Conversation not found | Return None, let caller handle |
| Message not found | Return None, let caller handle |
| Invalid attachment type | Raise ValidationError from Pydantic |
| Invalid role | Raise ValidationError from Pydantic |
| Database connection error | Propagate exception, let caller handle |
| Invalid ObjectId format | Raise ValidationError |

## Testing Strategy

### Unit Tests
- Test Pydantic model validation (valid/invalid data)
- Test repository methods with mocked database
- Test service business logic

### Property-Based Tests
Sử dụng **Hypothesis** library cho property-based testing:

- **Property 1-2**: Generate random conversations/messages, perform soft delete, verify behavior
- **Property 3**: Generate random messages, add to conversation, verify stats update
- **Property 4-5**: Generate random lists, verify ordering
- **Property 6**: Generate random content strings, verify title truncation
- **Property 7-8**: Generate random enum values, verify validation
- **Property 9**: Generate random messages, verify round-trip conversion
- **Property 10**: Generate random model data, verify field presence and types

### Test Configuration
- Minimum 100 iterations per property test
- Use pytest-asyncio for async tests
- Use mongomock or testcontainers for database tests
