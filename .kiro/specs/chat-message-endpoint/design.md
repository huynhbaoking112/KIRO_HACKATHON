# Design Document: Chat Message Endpoint

## Overview

Thiết kế endpoint cho phép user gửi message và nhận AI response qua Socket.IO streaming. Hệ thống sử dụng:
- FastAPI REST endpoint với BackgroundTasks
- LangGraph ReAct agent với OpenAI
- Socket.IO để stream response realtime
- Tích hợp với ConversationService đã có

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                 CLIENT                                        │
│  ┌─────────────────┐                              ┌─────────────────────┐    │
│  │   REST Client   │                              │   Socket.IO Client  │    │
│  │  POST /messages │                              │   Listen events     │    │
│  └────────┬────────┘                              └──────────▲──────────┘    │
└───────────┼──────────────────────────────────────────────────┼───────────────┘
            │                                                  │
            ▼                                                  │
┌───────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI SERVER                                    │
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                         API Layer (/api/v1/ai/chat.py)                  │  │
│  │  - Validate request                                                      │  │
│  │  - Create conversation if needed                                         │  │
│  │  - Save user message                                                     │  │
│  │  - Add background task                                                   │  │
│  │  - Return { user_message_id, conversation_id }                          │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                              │                                                 │
│                              ▼                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                    Service Layer (chat_service.py)                       │  │
│  │  - process_agent_response() [Background Task]                           │  │
│  │  - Load conversation history                                             │  │
│  │  - Call agent with streaming                                             │  │
│  │  - Emit socket events                                                    │  │
│  │  - Save assistant message                                                │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                              │                                                 │
│              ┌───────────────┼───────────────┐                                │
│              ▼               ▼               ▼                                │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                     │
│  │ Conversation  │  │    Agent      │  │  Socket.IO    │────────────────────►│
│  │   Service     │  │   Registry    │  │    Server     │     (emit events)   │
│  └───────────────┘  └───────────────┘  └───────────────┘                     │
│         │                   │                                                  │
│         ▼                   ▼                                                  │
│  ┌───────────────┐  ┌───────────────────────────────────┐                     │
│  │  Repository   │  │         Default Agent             │                     │
│  │    Layer      │  │  (LangGraph create_react_agent)   │                     │
│  └───────────────┘  │  + Calculator Tool                │                     │
│         │           └───────────────────────────────────┘                     │
│         ▼                   │                                                  │
│  ┌───────────────┐          ▼                                                  │
│  │   MongoDB     │  ┌───────────────┐                                         │
│  └───────────────┘  │ OpenAI (LLM)  │                                         │
│                     └───────────────┘                                         │
└───────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Chat API Endpoint

```python
# app/api/v1/ai/chat.py
router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/messages", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> SendMessageResponse:
    """Send message and trigger async agent processing."""
    pass
```

### 2. Chat Service

```python
# app/services/ai/chat_service.py
class ChatService:
    def __init__(
        self,
        conversation_service: ConversationService,
    ):
        self.conversation_service = conversation_service
    
    async def send_message(
        self,
        user_id: str,
        conversation_id: str | None,
        content: str,
    ) -> tuple[Message, str]:
        """Save user message and return (message, conversation_id)."""
        pass
    
    async def process_agent_response(
        self,
        user_id: str,
        conversation_id: str,
    ) -> None:
        """Background task: Stream agent response via socket."""
        pass
```

### 3. Default Agent

```python
# app/agents/implementations/default_agent/agent.py
from langgraph.prebuilt import create_react_agent

SYSTEM_PROMPT = """You are a helpful AI assistant..."""

def create_default_agent() -> CompiledGraph:
    """Create ReAct agent with calculator tool."""
    pass
```

### 4. Calculator Tool

```python
# app/agents/implementations/default_agent/tools.py
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    """Evaluate mathematical expression safely."""
    pass
```

### 5. LLM Factory

```python
# app/infrastructure/llm/factory.py
from langchain_openai import ChatOpenAI

def get_chat_openai(
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    streaming: bool = True,
) -> ChatOpenAI:
    """Create ChatOpenAI instance."""
    pass
```

### 6. Agent Registry

```python
# app/agents/registry.py
from functools import lru_cache

@lru_cache
def get_default_agent() -> CompiledGraph:
    """Get singleton default agent."""
    pass
```

## Data Models

### Request/Response Schemas

```python
# app/domain/schemas/chat.py

class SendMessageRequest(BaseModel):
    conversation_id: str | None = None
    content: str = Field(..., min_length=1, max_length=10000)

class SendMessageResponse(BaseModel):
    user_message_id: str
    conversation_id: str
```

### Socket Event Payloads

```python
class MessageStartedPayload(BaseModel):
    conversation_id: str

class MessageTokenPayload(BaseModel):
    conversation_id: str
    token: str

class MessageToolStartPayload(BaseModel):
    conversation_id: str
    tool_name: str
    tool_call_id: str

class MessageToolEndPayload(BaseModel):
    conversation_id: str
    tool_call_id: str
    result: str

class MessageCompletedPayload(BaseModel):
    conversation_id: str
    message_id: str
    content: str
    metadata: dict | None = None

class MessageFailedPayload(BaseModel):
    conversation_id: str
    error: str
```

### Socket Events Constants

```python
# app/common/event_socket.py

class ChatEvents:
    MESSAGE_STARTED = "chat:message:started"
    MESSAGE_TOKEN = "chat:message:token"
    MESSAGE_TOOL_START = "chat:message:tool_start"
    MESSAGE_TOOL_END = "chat:message:tool_end"
    MESSAGE_COMPLETED = "chat:message:completed"
    MESSAGE_FAILED = "chat:message:failed"
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: User Message Persistence
*For any* valid SendMessageRequest, the user message SHALL be saved to database before the API returns response.
**Validates: Requirements 1.4**

### Property 2: Conversation Creation
*For any* SendMessageRequest without conversation_id, a new conversation SHALL be created and its id returned in response.
**Validates: Requirements 1.2**

### Property 3: Background Task Execution
*For any* successful API call, the background task SHALL be triggered and emit at least MESSAGE_STARTED event.
**Validates: Requirements 1.5, 2.2**

### Property 4: Streaming Token Emission
*For any* agent response with content, the Chat_Service SHALL emit MESSAGE_TOKEN events for each token chunk.
**Validates: Requirements 2.3**

### Property 5: Assistant Message Persistence
*For any* completed agent response, the assistant message SHALL be saved to database with full content.
**Validates: Requirements 2.6**

### Property 6: Calculator Tool Safety
*For any* calculator input, the tool SHALL only evaluate expressions containing digits and basic operators (+, -, *, /, ., (, ), space).
**Validates: Requirements 3.4, 3.5**

### Property 7: Socket Event Room Targeting
*For any* socket event emitted during processing, it SHALL be sent to room "user:{user_id}" only.
**Validates: Requirements 6.7**

### Property 8: Error Event Emission
*For any* error during agent processing, the Chat_Service SHALL emit MESSAGE_FAILED event with error details.
**Validates: Requirements 2.8**

## Error Handling

| Error Case | Handling |
|------------|----------|
| Invalid conversation_id | Return 404 Not Found |
| Empty content | Return 422 Validation Error (Pydantic) |
| Agent streaming error | Emit MESSAGE_FAILED, log error |
| Database error | Emit MESSAGE_FAILED, log error |
| OpenAI API error | Emit MESSAGE_FAILED, log error |
| Calculator invalid expression | Return error string (not exception) |

## Testing Strategy

### Unit Tests
- Test SendMessageRequest validation
- Test calculator tool with valid/invalid expressions
- Test ChatService methods with mocked dependencies

### Integration Tests
- Test full flow: API → Service → Agent → Socket
- Test conversation creation flow
- Test error handling flows

### Property-Based Tests
Sử dụng **Hypothesis** library:

- **Property 6**: Generate random strings, verify calculator rejects unsafe inputs
- **Property 1, 5**: Generate random messages, verify persistence

### Test Configuration
- Use pytest-asyncio for async tests
- Mock Socket.IO for unit tests
- Mock OpenAI for deterministic tests
