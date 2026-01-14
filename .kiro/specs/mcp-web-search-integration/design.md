# Design Document: MCP Web Search Integration

## Overview

Tích hợp DuckDuckGo MCP Server vào hệ thống AI Chat thông qua `langchain-mcp-adapters`. Solution này cho phép cả Data Agent và Chat Agent có khả năng search web và lấy content từ URLs mà không cần tự implement web scraping logic.

### Key Design Decisions

1. **Sử dụng langchain-mcp-adapters**: Native integration với LangChain/LangGraph, MCP servers spawn tự động như subprocess
2. **Singleton MCP Client**: Một instance quản lý tất cả MCP servers, tránh spawn nhiều processes
3. **Upgrade chat_node thành chat_agent**: Để có tool calling capability
4. **Centralized configuration**: MCP servers config tập trung, dễ mở rộng

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AI SERVICE                                   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Chat Workflow                                │ │
│  │                                                                 │ │
│  │   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │ │
│  │   │   Intent    │────▶│ chat_agent  │     │ data_agent  │      │ │
│  │   │ Classifier  │     │   (NEW)     │     │ (UPDATED)   │      │ │
│  │   └─────────────┘     └──────┬──────┘     └──────┬──────┘      │ │
│  │                              │                   │              │ │
│  │                              └─────────┬─────────┘              │ │
│  │                                        │                        │ │
│  │                                        ▼                        │ │
│  │                         ┌──────────────────────────┐            │ │
│  │                         │   MCP Tools Manager      │            │ │
│  │                         │   (Singleton)            │            │ │
│  │                         └────────────┬─────────────┘            │ │
│  └──────────────────────────────────────┼──────────────────────────┘ │
│                                         │                            │
│                                         ▼                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                 MultiServerMCPClient                            │ │
│  │  ┌─────────────────────┐    ┌─────────────────────┐            │ │
│  │  │  DuckDuckGo MCP     │    │  Future MCP         │            │ │
│  │  │  (subprocess)       │    │  Servers...         │            │ │
│  │  │                     │    │                     │            │ │
│  │  │  • search()         │    │                     │            │ │
│  │  │  • fetch_content()  │    │                     │            │ │
│  │  └─────────────────────┘    └─────────────────────┘            │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. MCP Configuration (`app/config/mcp.py`)

```python
from typing import TypedDict, Literal, Optional
from dataclasses import dataclass

class StdioTransportConfig(TypedDict):
    transport: Literal["stdio"]
    command: str
    args: list[str]
    enabled: bool

class HttpTransportConfig(TypedDict):
    transport: Literal["http"]
    url: str
    headers: Optional[dict[str, str]]
    enabled: bool

MCPServerConfig = StdioTransportConfig | HttpTransportConfig

MCP_SERVERS: dict[str, MCPServerConfig] = {
    "ddg-search": {
        "transport": "stdio",
        "command": "uvx",
        "args": ["duckduckgo-mcp-server"],
        "enabled": True,
    }
}
```

### 2. MCP Tools Manager (`app/infrastructure/mcp/manager.py`)

```python
from functools import lru_cache
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool

class MCPToolsManager:
    """Singleton manager for MCP server connections and tools."""
    
    _instance: Optional["MCPToolsManager"] = None
    _client: Optional[MultiServerMCPClient] = None
    _tools: list[BaseTool] = []
    
    @classmethod
    def get_instance(cls) -> "MCPToolsManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def initialize(self, config: dict[str, MCPServerConfig]) -> None:
        """Initialize MCP client with configured servers."""
        # Filter enabled servers
        enabled_servers = {
            name: {k: v for k, v in cfg.items() if k != "enabled"}
            for name, cfg in config.items()
            if cfg.get("enabled", True)
        }
        
        self._client = MultiServerMCPClient(enabled_servers)
        self._tools = await self._client.get_tools()
    
    def get_tools(self) -> list[BaseTool]:
        """Get all loaded MCP tools."""
        return self._tools
    
    async def reload(self, config: dict[str, MCPServerConfig]) -> None:
        """Reload MCP connections with new config."""
        await self.initialize(config)

@lru_cache
def get_mcp_tools_manager() -> MCPToolsManager:
    """Get singleton MCPToolsManager instance."""
    return MCPToolsManager.get_instance()
```

### 3. Updated Data Agent (`app/agents/implementations/data_agent/agent.py`)

```python
from app.infrastructure.mcp.manager import get_mcp_tools_manager

def create_data_agent(user_connections: list[dict[str, Any]]) -> CompiledStateGraph:
    """Create data agent with both data tools and MCP tools."""
    
    llm = get_chat_openai(temperature=0.3, streaming=True, max_tokens=4096)
    
    # Existing data tools
    data_tools = [
        create_get_data_schema_tool(user_connections),
        create_aggregate_data_tool(user_connections),
        create_get_top_items_tool(user_connections),
        create_compare_periods_tool(user_connections),
        create_execute_aggregation_tool(user_connections),
    ]
    
    # MCP tools (web search, fetch content)
    mcp_manager = get_mcp_tools_manager()
    mcp_tools = mcp_manager.get_tools()
    
    # Combine all tools
    all_tools = data_tools + mcp_tools
    
    # Updated system prompt
    schema_context = format_schema_context(user_connections)
    system_prompt = DATA_AGENT_SYSTEM_PROMPT_WITH_WEB.format(
        schema_context=schema_context
    )
    
    agent = create_react_agent(model=llm, tools=all_tools, prompt=system_prompt)
    return agent
```

### 4. New Chat Agent (`app/agents/implementations/chat_agent/agent.py`)

```python
from langgraph.prebuilt import create_react_agent
from app.infrastructure.mcp.manager import get_mcp_tools_manager

def create_chat_agent() -> CompiledStateGraph:
    """Create chat agent with web search capability."""
    
    llm = get_chat_openai(temperature=0.7, streaming=True)
    
    # MCP tools only for chat agent
    mcp_manager = get_mcp_tools_manager()
    mcp_tools = mcp_manager.get_tools()
    
    system_prompt = CHAT_AGENT_SYSTEM_PROMPT
    
    agent = create_react_agent(model=llm, tools=mcp_tools, prompt=system_prompt)
    return agent
```

### 5. Updated Chat Node (`app/graphs/workflows/chat_workflow/nodes/chat_node.py`)

```python
async def chat_node(state: ChatWorkflowState) -> dict:
    """Handle general conversation with web search capability."""
    
    user_id = state.get("user_id", "")
    conversation_id = state.get("conversation_id", "")
    
    try:
        # Create chat agent with MCP tools
        agent = create_chat_agent()
        
        # Build messages
        agent_messages = _build_agent_messages(state.get("messages", []))
        
        # Stream agent execution with tool events
        response = await _stream_chat_agent_execution(
            agent=agent,
            messages=agent_messages,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        
        return {"agent_response": response}
        
    except Exception:
        logger.exception("Chat node failed")
        return {"agent_response": "Xin lỗi, tôi gặp sự cố. Vui lòng thử lại."}
```

## Data Models

### MCP Tool Response Types

```python
from typing import TypedDict

class SearchResult(TypedDict):
    title: str
    url: str
    snippet: str

class WebSearchResponse(TypedDict):
    results: list[SearchResult]
    query: str

class FetchContentResponse(TypedDict):
    url: str
    content: str
    title: Optional[str]
```

### Updated ChatWorkflowState

```python
class ChatWorkflowState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str
    conversation_id: str
    user_connections: list[dict]
    intent: Optional[str]
    agent_response: Optional[str]
    tool_calls: list[ToolCallRecord]  # Track MCP tool calls too
    error: Optional[str]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: MCP Initialization Completeness

*For any* valid MCP server configuration with N enabled servers, after initialization, the MCP_Tools_Manager SHALL have loaded tools from all N servers and the total tool count SHALL be greater than zero.

**Validates: Requirements 1.1, 1.3, 1.5**

### Property 2: Singleton Consistency

*For any* number of calls to get_mcp_tools_manager(), all calls SHALL return the same instance (identity equality).

**Validates: Requirements 1.2**

### Property 3: Agent Tool Inclusion

*For any* agent creation (data_agent or chat_agent), the resulting agent's tool list SHALL include all MCP tools from MCP_Tools_Manager.

**Validates: Requirements 3.1, 4.2**

### Property 4: Tool Event Emission

*For any* tool execution during chat_agent streaming, the system SHALL emit exactly one tool_start event before execution and exactly one tool_end event after execution via Socket.IO.

**Validates: Requirements 4.6**

### Property 5: Disabled Server Exclusion

*For any* MCP server configuration where a server has enabled=False, that server SHALL NOT be initialized and its tools SHALL NOT be available.

**Validates: Requirements 5.5**

## Error Handling

### MCP Server Connection Failures

```python
async def initialize(self, config: dict) -> None:
    try:
        self._client = MultiServerMCPClient(enabled_servers)
        self._tools = await self._client.get_tools()
    except Exception as e:
        logger.error(f"MCP initialization failed: {e}")
        self._tools = []  # Continue without MCP tools
```

### Tool Execution Timeout

```python
# Configure timeout in MCP client
client = MultiServerMCPClient(
    servers,
    timeout=30.0  # 30 second timeout
)
```

### Graceful Degradation

- If MCP tools unavailable → Agents work with remaining tools
- If web search fails → Agent informs user, suggests alternatives
- If fetch_content fails → Agent tries other URLs or summarizes from snippets

## Testing Strategy

### Unit Tests

1. **MCP Configuration Tests**
   - Valid stdio config parsing
   - Valid http config parsing
   - Invalid config rejection

2. **MCP Tools Manager Tests**
   - Singleton pattern verification
   - Tool loading from mock MCP server
   - Disabled server filtering

3. **Agent Creation Tests**
   - Data agent includes MCP tools
   - Chat agent includes MCP tools
   - Tool count verification

### Property-Based Tests

Using `hypothesis` library:

1. **Property 1 Test**: Generate random valid configs, verify tool loading
2. **Property 2 Test**: Multiple concurrent calls return same instance
3. **Property 3 Test**: Random agent creation includes MCP tools
4. **Property 5 Test**: Random enabled/disabled configs, verify exclusion

### Integration Tests

1. **End-to-end web search flow**
   - User asks question → Agent uses search → Response contains search results

2. **Tool event streaming**
   - Verify Socket.IO events emitted during tool execution

3. **Error recovery**
   - MCP server crash → System continues
   - Network timeout → Graceful error message

### Test Configuration

```python
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py

# Property test settings
hypothesis_profile = default
hypothesis_seed = 12345
```

Property tests should run minimum 100 iterations to ensure coverage.
