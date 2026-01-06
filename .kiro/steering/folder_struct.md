---
inclusion: manual
---

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
├── infrastructure/            # External integrations
├── domain/                    # Domain models & schemas
├── prompts/                   # Prompt templates
├── workers/                   # Background jobs
└── common/                    # Shared utilities
```

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
- Services orchestrate agents, graphs, and infrastructure
- Keep AI services separate from business services
- Services should be stateless
- Use dependency injection for infrastructure

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

### `/common` - Shared Utilities
- Cross-cutting concerns only
- `exceptions.py` - Custom exceptions
- `streaming.py` - SSE/WebSocket helpers
- `callbacks.py` - LangChain callbacks
- No business logic here

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
