<!-- ---
inclusion: manual
--- -->

# Project Structure Guidelines

This document defines the folder structure conventions for the AI Service project built with FastAPI, LangChain, and LangGraph.

## Core Principles

- **Domain-driven organization**: Group by feature/domain, not by file type
- **Separation of concerns**: Keep AI logic, business logic, and infrastructure separate
- **Scalability**: Structure supports growth from MVP to enterprise
- **Discoverability**: New developers can find code intuitively

## Directory Structure

```
app/
├── main.py                    # FastAPI entry point - DO NOT add business logic here
├── config/                    # Configuration only
├── api/                       # HTTP layer only - thin controllers
├── agents/                    # LangChain Agents
├── graphs/                    # LangGraph Workflows
├── chains/                    # Simple LangChain Chains
├── services/                  # Business logic orchestration
├── repo/                      # Repository layer - data access
├── infrastructure/            # External integrations
├── domain/                    # Domain models & schemas
├── prompts/                   # Prompt templates
├── socket_gateway/            # Real-time WebSocket/Socket.IO layer
├── workers/                   # Background jobs & async tasks
└── common/                    # Shared utilities
```

## Request Flow Architecture

```
API (Controller) → Service → Repository → Infrastructure
```

- **API/Controller**: Receive request, validate input, return response
- **Service**: Handle business logic, orchestrate multiple repos if needed
- **Repository**: Data access layer, CRUD operations
- **Infrastructure**: Database connections, external services

## Module Conventions

### `/api` - HTTP Layer
- Routes should be thin controllers - delegate to services
- Version all endpoints under `/v1/`, `/v2/`
- Separate AI endpoints (`/api/v1/ai/`) from business endpoints (`/api/v1/business/`)
- Use `deps.py` for shared FastAPI dependencies
- Use `middleware.py` for cross-cutting concerns

```python
# GOOD: Thin controller
@router.post("/chat")
async def chat(request: ChatRequest, service: ChatService = Depends(get_chat_service)):
    return await service.process(request)

# BAD: Business logic in route
@router.post("/chat")
async def chat(request: ChatRequest):
    # Don't put LLM calls, validation, or business logic here
```

### `/agents` - LangChain Agents
Structure:
```
agents/
├── registry.py                # Agent factory/registry
├── base/
│   ├── base_agent.py          # Abstract base class
│   └── types.py               # Agent enums, types
├── implementations/           # Concrete agents
│   └── {agent_name}/
│       ├── agent.py           # Agent implementation
│       ├── prompts.py         # Agent-specific prompts
│       └── tools.py           # Agent-specific tools
└── tools/                     # Shared tools across agents
```

Rules:
- Each agent in its own subdirectory under `implementations/`
- Agent-specific prompts stay with the agent, not in `/prompts`
- Shared tools go in `agents/tools/`
- Register all agents in `registry.py`

### `/graphs` - LangGraph Workflows
Structure:
```
graphs/
├── registry.py                # Graph factory/registry
├── base/
│   ├── base_graph.py          # Abstract base graph
│   ├── state.py               # Shared state definitions
│   └── types.py               # Graph types
├── workflows/                 # Concrete graphs
│   └── {workflow_name}/
│       ├── graph.py           # Graph definition
│       ├── state.py           # Workflow-specific state
│       └── nodes/             # Node implementations
│           ├── {node_name}.py
│           └── ...
└── nodes/                     # Shared/reusable nodes
```

Rules:
- One workflow = one subdirectory under `workflows/`
- Each node is a separate file in `nodes/`
- Workflow-specific state in workflow's `state.py`
- Shared nodes go in `graphs/nodes/`

### `/chains` - Simple LangChain Chains
- For simple, linear LLM operations (summarization, translation, extraction)
- One file per chain type
- If chain becomes complex, promote to a graph

### `/services` - Business Logic
Structure:
```
services/
├── ai/                        # AI-related services
│   ├── chat_service.py
│   ├── agent_service.py       # Orchestrates agents
│   ├── graph_service.py       # Orchestrates graphs
│   └── knowledge_service.py
└── business/                  # Non-AI services
    ├── user_service.py
    └── project_service.py
```

Rules:
- Services orchestrate agents, graphs, and repositories
- Keep AI services separate from business services
- Services should be stateless
- Use dependency injection for repositories

### `/repo` - Repository Layer (Data Access)
- Layer for direct database operations
- Each entity has a corresponding repository file
- Contains basic CRUD operations

```python
# Example: user_repo.py
class UserRepository:
    def __init__(self, db: MongoDB):
        self.collection = db.get_collection("users")
    
    async def find_by_id(self, user_id: str) -> Optional[User]:
        doc = await self.collection.find_one({"_id": user_id})
        return User(**doc) if doc else None
    
    async def create(self, user: User) -> User:
        await self.collection.insert_one(user.dict())
        return user
```

### `/infrastructure` - External Integrations
Structure:
```
infrastructure/
├── llm/                       # LLM providers
│   ├── factory.py             # LLM factory pattern
│   ├── openai_client.py
│   └── anthropic_client.py
├── vector_store/              # Vector databases
│   ├── factory.py
│   ├── qdrant.py
│   └── pinecone.py
├── embeddings/                # Embedding providers
├── database/                  # Traditional databases
├── cache/                     # Caching (Redis)
└── messaging/                 # Message queues
```

Rules:
- Use factory pattern for swappable implementations
- Each provider in its own file
- Abstract interfaces in `factory.py`
- Never import infrastructure directly in routes - use services

### `/domain` - Domain Models
Structure:
```
domain/
├── models/                    # Database/domain models
│   ├── conversation.py
│   └── message.py
└── schemas/                   # Pydantic schemas (API contracts)
    ├── chat.py
    └── agent.py
```

Rules:
- `models/` for database entities and domain objects
- `schemas/` for Pydantic models (request/response)
- Keep schemas close to their domain

### `/prompts` - Prompt Templates
Structure:
```
prompts/
├── system/                    # System prompts
├── templates/                 # Reusable templates
└── loader.py                  # Prompt loading utilities
```

Rules:
- Agent-specific prompts stay with agents
- Only shared/reusable prompts here
- Use `loader.py` for dynamic prompt loading

### `/workers` - Background Jobs
- One file per worker type
- Use for async operations: embedding, indexing, cleanup
- Keep workers thin - delegate to services

Structure:
```
workers/
├── __init__.py
├── sheet_sync_worker.py       # Google Sheets sync worker
├── embedding_worker.py        # Vector embedding jobs
└── cleanup_worker.py          # Data cleanup tasks
```

Rules:
- Each worker handles one specific job type
- Workers consume from Redis Queue (or other message broker)
- Delegate business logic to services - workers only orchestrate
- Use proper error handling and retry mechanisms
- Log job progress and failures for observability

```python
# Example: sheet_sync_worker.py
class SheetSyncWorker:
    def __init__(self, queue: RedisQueue, crawler_service: CrawlerService):
        self.queue = queue
        self.crawler_service = crawler_service
    
    async def process_job(self, job_data: dict) -> None:
        """Process a single sync job - delegate to service."""
        connection_id = job_data["connection_id"]
        await self.crawler_service.sync_sheet(connection_id)
```

### `/socket_gateway` - Real-time Communication Layer
Structure:
```
socket_gateway/
├── __init__.py                # Export sio instance
├── server.py                  # Socket.IO AsyncServer setup & core events
├── auth.py                    # JWT authentication for WebSocket
├── manager.py                 # Connection/room management utilities
└── worker_gateway.py          # Bridge between workers and Socket.IO
```

Rules:
- `server.py` contains Socket.IO server instance and core event handlers (connect/disconnect)
- `auth.py` handles JWT token validation for WebSocket connections
- `manager.py` provides utilities for room management, broadcasting
- `worker_gateway.py` enables background workers to emit events to connected clients
- Keep event handlers thin - delegate business logic to services
- Use rooms for user-specific or group messaging

```python
# Example: server.py
import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

@sio.event
async def connect(sid: str, environ: dict, auth: dict | None = None) -> None:
    """Authenticate and join user to personal room."""
    user_data = await authenticate(auth, environ)
    if user_data is None:
        raise ConnectionRefusedError("Unauthorized")
    await sio.enter_room(sid, f"user:{user_data['user_id']}")
```

```python
# Example: worker_gateway.py - Cross-process emit
class WorkerGateway:
    """Enables workers to emit Socket.IO events via Redis pub/sub."""
    
    async def emit_to_user(self, user_id: str, event: str, data: dict) -> None:
        """Publish event to Redis for Socket.IO server to broadcast."""
        await self.redis.publish(
            "socket_events",
            {"room": f"user:{user_id}", "event": event, "data": data}
        )
```

Integration with FastAPI (in `main.py`):
```python
from app.socket_gateway import sio

# Combine FastAPI with Socket.IO
combined_app = socketio.ASGIApp(sio, other_asgi_app=app)
```

### `/common` - Shared Utilities
Structure:
```
common/
├── __init__.py
├── exceptions.py              # Custom exceptions
├── repo.py                    # Repository factory functions (singleton)
├── service.py                 # Service factory functions (singleton)
└── event_socket.py            # Socket event constants
```

Rules:
- Cross-cutting concerns only - no business logic here
- `repo.py` - Factory functions for repository singletons using `@lru_cache`
- `service.py` - Factory functions for service singletons using `@lru_cache`
- `event_socket.py` - Centralized socket event name constants to avoid hardcoding

```python
# Example: repo.py - Repository factory with singleton pattern
from functools import lru_cache

@lru_cache
def get_user_repo() -> UserRepository:
    """Get singleton UserRepository instance."""
    db = MongoDB.get_db()
    return UserRepository(db)
```

```python
# Example: service.py - Service factory with singleton pattern
from functools import lru_cache

@lru_cache
def get_crawler_service() -> SheetCrawlerService:
    """Get singleton SheetCrawlerService instance."""
    return SheetCrawlerService(
        sheet_client=get_google_sheet_client(),
        connection_repo=get_sheet_connection_repo(),
        sync_state_repo=get_sheet_sync_state_repo(),
        data_repo=get_sheet_data_repo(),
    )
```

```python
# Example: event_socket.py - Socket event constants
class SheetSyncEvents:
    """Socket events for sheet synchronization."""
    STARTED = "sheet:sync:started"
    COMPLETED = "sheet:sync:completed"
    FAILED = "sheet:sync:failed"
    PROGRESS = "sheet:sync:progress"
```

## File Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Modules | snake_case | `chat_service.py` |
| Classes | PascalCase | `ChatService` |
| Functions | snake_case | `process_message()` |
| Constants | UPPER_SNAKE | `MAX_TOKENS` |
| Pydantic schemas | PascalCase + suffix | `ChatRequest`, `ChatResponse` |

## Import Rules

```python
# GOOD: Explicit imports
from app.services.ai.chat_service import ChatService
from app.infrastructure.llm.factory import get_llm

# BAD: Relative imports across modules
from ...infrastructure.llm import get_llm

# GOOD: Cross-package imports with explicit module
from app.agents.tools.search import SearchTool
```

## Testing Structure

```
tests/
├── unit/                      # Unit tests mirror app structure
│   ├── agents/
│   ├── graphs/
│   └── services/
├── integration/               # Integration tests
└── e2e/                       # End-to-end tests
```

## Anti-Patterns to Avoid

1. **God modules**: Don't put all agents in one file
2. **Circular imports**: Use dependency injection
3. **Business logic in routes**: Routes should only handle HTTP
4. **Direct infrastructure access**: Always go through services
5. **Mixing AI and business logic**: Keep them in separate service directories
