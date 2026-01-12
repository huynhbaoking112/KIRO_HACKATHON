# Design Document: AI Chat Agent

## Overview

AI Chat Agent là một LangGraph workflow cho phép người dùng query dữ liệu kinh doanh bằng ngôn ngữ tự nhiên. Hệ thống sử dụng multi-node architecture với intent classification để route requests đến handler phù hợp.

### Key Design Decisions

1. **LangGraph Workflow**: Sử dụng StateGraph với conditional edges để route based on intent
2. **Hybrid Tools**: Simple tools cho common queries + execute_aggregation cho complex cases
3. **Reuse Existing Infrastructure**: conversation_repo, message_repo, Socket.IO streaming
4. **Data Isolation**: Filter by user's connection_ids trong mọi query

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              LANGGRAPH CHAT WORKFLOW                                 │
│                                                                                      │
│  ┌─────────┐                                                                        │
│  │  START  │                                                                        │
│  └────┬────┘                                                                        │
│       │                                                                              │
│       ▼                                                                              │
│  ┌─────────────────────┐                                                            │
│  │  INTENT CLASSIFIER  │◄─── prompts/system/intent_classifier.py                    │
│  │  (LLM Classification)│                                                            │
│  └──────────┬──────────┘                                                            │
│             │                                                                        │
│             │ intent = ?                                                             │
│     ┌───────┴───────┬───────────────┐                                               │
│     ▼               ▼               ▼                                               │
│  ┌──────┐       ┌──────┐       ┌──────────┐                                         │
│  │"chat"│       │"data"│       │"unclear" │                                         │
│  └──┬───┘       └──┬───┘       └────┬─────┘                                         │
│     │              │                │                                               │
│     ▼              ▼                ▼                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                                  │
│  │  CHAT NODE  │  │ DATA AGENT  │  │CLARIFY NODE │                                  │
│  │  (General)  │  │  (ReAct)    │  │             │                                  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                                  │
│         │                │                │                                          │
│         │         ┌──────┴──────┐         │                                          │
│         │         │   TOOLS     │         │                                          │
│         │         │ - schema    │         │                                          │
│         │         │ - aggregate │         │                                          │
│         │         │ - top_items │         │                                          │
│         │         │ - compare   │         │                                          │
│         │         │ - execute   │         │                                          │
│         │         └──────┬──────┘         │                                          │
│         │                │                │                                          │
│         └────────────────┼────────────────┘                                          │
│                          │                                                           │
│                          ▼                                                           │
│                    ┌─────────────────────────┐                                      │
│                    │   RESPONSE FORMATTER    │                                      │
│                    │   (Format final answer) │                                      │
│                    └───────────┬─────────────┘                                      │
│                                │                                                     │
│                                ▼                                                     │
│                          ┌─────────┐                                                │
│                          │   END   │                                                │
│                          └─────────┘                                                │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Graph Layer

#### Chat Workflow (`app/graphs/workflows/chat_workflow/graph.py`)

```python
class ChatWorkflow:
    def __init__(self):
        self.graph = StateGraph(ChatWorkflowState)
        self._build_graph()
    
    def _build_graph(self):
        # Add nodes
        self.graph.add_node("intent_classifier", intent_classifier_node)
        self.graph.add_node("chat_node", chat_node)
        self.graph.add_node("data_agent_node", data_agent_node)
        self.graph.add_node("clarify_node", clarify_node)
        self.graph.add_node("response_formatter", response_formatter_node)
        
        # Add edges
        self.graph.add_edge(START, "intent_classifier")
        self.graph.add_conditional_edges(
            "intent_classifier",
            route_by_intent,
            {
                "chat": "chat_node",
                "data_query": "data_agent_node",
                "unclear": "clarify_node",
            }
        )
        self.graph.add_edge("chat_node", "response_formatter")
        self.graph.add_edge("data_agent_node", "response_formatter")
        self.graph.add_edge("clarify_node", "response_formatter")
        self.graph.add_edge("response_formatter", END)
    
    def compile(self) -> CompiledStateGraph:
        return self.graph.compile()
```

#### Chat Workflow State (`app/graphs/workflows/chat_workflow/state.py`)

```python
class ChatWorkflowState(TypedDict):
    messages: Annotated[list, add_messages]  # Conversation history
    user_id: str
    conversation_id: str
    user_connections: list[dict]  # User's sheet connections with schemas
    intent: Optional[str]  # "data_query", "chat", "unclear"
    agent_response: Optional[str]  # Response from agent/node
    tool_calls: list[dict]  # Tool call history for streaming
    final_response: Optional[str]  # Formatted final response
    error: Optional[str]
```

### 2. Node Implementations

#### Intent Classifier Node (`app/graphs/workflows/chat_workflow/nodes/intent_classifier.py`)

```python
async def intent_classifier_node(state: ChatWorkflowState) -> dict:
    """
    Classify user intent using LLM.
    Returns: {"intent": "data_query" | "chat" | "unclear"}
    """
    pass
```

#### Chat Node (`app/graphs/workflows/chat_workflow/nodes/chat_node.py`)

```python
async def chat_node(state: ChatWorkflowState) -> dict:
    """
    Handle general conversation.
    Returns: {"agent_response": str}
    """
    pass
```

#### Data Agent Node (`app/graphs/workflows/chat_workflow/nodes/data_agent_node.py`)

```python
async def data_agent_node(state: ChatWorkflowState) -> dict:
    """
    Execute Data Agent with tools.
    Returns: {"agent_response": str, "tool_calls": list}
    """
    pass
```

#### Clarify Node (`app/graphs/workflows/chat_workflow/nodes/clarify_node.py`)

```python
async def clarify_node(state: ChatWorkflowState) -> dict:
    """
    Ask user for clarification.
    Returns: {"agent_response": str}
    """
    pass
```

#### Response Formatter Node (`app/graphs/workflows/chat_workflow/nodes/response_formatter.py`)

```python
async def response_formatter_node(state: ChatWorkflowState) -> dict:
    """
    Format final response for user.
    Returns: {"final_response": str}
    """
    pass
```

### 3. Agent Layer

#### Data Agent (`app/agents/implementations/data_agent/agent.py`)

```python
def create_data_agent(user_connections: list[dict]) -> CompiledStateGraph:
    """
    Create ReAct agent with data query tools.
    
    Args:
        user_connections: List of user's sheet connections with schemas
    
    Returns:
        Compiled LangGraph agent
    """
    llm = get_chat_openai()
    tools = [
        create_get_data_schema_tool(user_connections),
        create_aggregate_data_tool(user_connections),
        create_get_top_items_tool(user_connections),
        create_compare_periods_tool(user_connections),
        create_execute_aggregation_tool(user_connections),
    ]
    
    system_prompt = DATA_AGENT_SYSTEM_PROMPT.format(
        schema_context=format_schema_context(user_connections)
    )
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
    )
    
    return agent
```

#### Data Agent Tools (`app/agents/implementations/data_agent/tools.py`)

```python
def create_get_data_schema_tool(user_connections: list[dict]):
    @tool
    def get_data_schema(connection_name: Optional[str] = None) -> str:
        """Get schema of user's data connections."""
        pass
    return get_data_schema

def create_aggregate_data_tool(user_connections: list[dict]):
    @tool
    def aggregate_data(
        connection_name: str,
        operation: str,  # sum, count, avg, min, max
        field: Optional[str] = None,
        group_by: Optional[str] = None,
        filters: Optional[dict] = None,
        date_field: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> str:
        """Perform aggregation on data."""
        pass
    return aggregate_data

def create_get_top_items_tool(user_connections: list[dict]):
    @tool
    def get_top_items(
        connection_name: str,
        sort_field: str,
        sort_order: str = "desc",
        limit: int = 10,
        group_by: Optional[str] = None,
        aggregate_field: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> str:
        """Get top N items by field."""
        pass
    return get_top_items

def create_compare_periods_tool(user_connections: list[dict]):
    @tool
    def compare_periods(
        connection_name: str,
        operation: str,
        field: Optional[str] = None,
        date_field: str,
        period1_from: str,
        period1_to: str,
        period2_from: str,
        period2_to: str,
        group_by: Optional[str] = None,
    ) -> str:
        """Compare metrics between two time periods."""
        pass
    return compare_periods

def create_execute_aggregation_tool(user_connections: list[dict]):
    @tool
    def execute_aggregation(
        connection_name: str,
        pipeline: list[dict],
        description: str,
    ) -> str:
        """Execute custom MongoDB aggregation pipeline."""
        pass
    return execute_aggregation
```

### 4. Service Layer

#### Data Query Service (`app/services/ai/data_query_service.py`)

```python
class DataQueryService:
    def __init__(
        self,
        connection_repo: SheetConnectionRepository,
        data_repo: SheetDataRepository,
    ):
        self.connection_repo = connection_repo
        self.data_repo = data_repo
    
    async def get_user_connections(self, user_id: str) -> list[dict]:
        """Get all connections with schemas for a user."""
        pass
    
    async def aggregate(
        self,
        connection_id: str,
        operation: str,
        field: Optional[str],
        group_by: Optional[str],
        filters: Optional[dict],
    ) -> list[dict]:
        """Execute aggregation query."""
        pass
    
    async def get_top_items(
        self,
        connection_id: str,
        sort_field: str,
        sort_order: str,
        limit: int,
        group_by: Optional[str],
        aggregate_field: Optional[str],
        filters: Optional[dict],
    ) -> list[dict]:
        """Get top N items."""
        pass
    
    async def execute_pipeline(
        self,
        connection_id: str,
        pipeline: list[dict],
        user_connection_ids: list[str],
    ) -> list[dict]:
        """Execute validated aggregation pipeline."""
        pass
```

#### Pipeline Validator (`app/services/ai/pipeline_validator.py`)

```python
class PipelineValidator:
    ALLOWED_STAGES = {
        "$match", "$group", "$sort", "$limit",
        "$project", "$lookup", "$unwind", "$count"
    }
    
    BLOCKED_STAGES = {"$out", "$merge", "$delete"}
    
    MAX_LIMIT = 1000
    
    def validate(
        self,
        pipeline: list[dict],
        user_connection_ids: list[str],
    ) -> list[dict]:
        """
        Validate and sanitize pipeline.
        Raises ValidationError if invalid.
        Returns sanitized pipeline.
        """
        pass
```

#### Chat Service Update (`app/services/ai/chat_service.py`)

```python
class ChatService:
    def __init__(
        self,
        conversation_service: ConversationService,
        data_query_service: DataQueryService,
    ):
        self.conversation_service = conversation_service
        self.data_query_service = data_query_service
    
    async def process_message(
        self,
        user_id: str,
        conversation_id: str,
    ) -> None:
        """
        Process message using ChatWorkflow graph.
        Streams responses via Socket.IO.
        """
        # Load user connections
        user_connections = await self.data_query_service.get_user_connections(user_id)
        
        # Load conversation history
        messages = await self.conversation_service.get_langchain_messages(conversation_id)
        
        # Create and run workflow
        workflow = ChatWorkflow(user_connections)
        graph = workflow.compile()
        
        # Stream execution
        async for event in graph.astream_events(
            {
                "messages": messages,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "user_connections": user_connections,
            },
            version="v2",
        ):
            # Emit socket events for streaming
            pass
```

## Data Models

### Workflow State (`app/graphs/workflows/chat_workflow/state.py`)

```python
from typing import Annotated, Optional, TypedDict
from langgraph.graph.message import add_messages

class ChatWorkflowState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str
    conversation_id: str
    user_connections: list[dict]
    intent: Optional[str]
    agent_response: Optional[str]
    tool_calls: list[dict]
    final_response: Optional[str]
    error: Optional[str]
```

### Tool Call Record

```python
class ToolCallRecord(TypedDict):
    tool_name: str
    tool_call_id: str
    arguments: dict
    result: Optional[str]
    error: Optional[str]
```


## Prompts

### Intent Classifier Prompt (`app/prompts/system/intent_classifier.py`)

```python
INTENT_CLASSIFIER_PROMPT = """Bạn là một classifier phân loại ý định người dùng.

Phân loại tin nhắn của người dùng vào một trong các loại sau:
- "data_query": Câu hỏi về dữ liệu, số liệu, thống kê, phân tích
- "chat": Chào hỏi, trò chuyện thông thường, hỏi về khả năng của hệ thống
- "unclear": Câu hỏi không rõ ràng, cần làm rõ thêm

Ví dụ "data_query":
- "Tổng doanh thu tháng này là bao nhiêu?"
- "Top 5 sản phẩm bán chạy nhất?"
- "So sánh doanh thu tuần này với tuần trước"
- "Có bao nhiêu đơn hàng từ Shopee?"

Ví dụ "chat":
- "Xin chào"
- "Bạn có thể làm gì?"
- "Cảm ơn bạn"

Ví dụ "unclear":
- "Cho tôi xem"
- "Cái đó"
- "Hơn"

Chỉ trả lời một trong ba giá trị: "data_query", "chat", hoặc "unclear"
"""
```

### Data Agent Prompt (`app/prompts/system/data_agent.py`)

```python
DATA_AGENT_SYSTEM_PROMPT = """Bạn là trợ lý phân tích dữ liệu kinh doanh.

## Data Sources của user:
{schema_context}

## Tools của bạn:

### Simple Tools (ưu tiên sử dụng):
- get_data_schema: Xem danh sách connections và fields
- aggregate_data: Tính sum/count/avg/min/max với filters và group_by
- get_top_items: Lấy top N items theo field
- compare_periods: So sánh 2 khoảng thời gian

### Advanced Tool (khi cần query phức tạp):
- execute_aggregation: Chạy MongoDB aggregation pipeline tùy chỉnh
  - Sử dụng khi cần JOIN giữa nhiều bảng ($lookup)
  - Sử dụng khi simple tools không đủ

## Quy tắc:
1. Luôn gọi get_data_schema trước nếu chưa biết schema
2. Ưu tiên simple tools trước
3. Chỉ dùng execute_aggregation khi thực sự cần
4. Nếu query fail, đọc error message và thử lại (tối đa 3 lần)
5. Trả lời bằng tiếng Việt
6. Format số tiền: 1.000.000 VND
"""
```

### Chat Node Prompt (`app/prompts/system/chat_node.py`)

```python
CHAT_NODE_PROMPT = """Bạn là trợ lý AI thân thiện, hỗ trợ phân tích dữ liệu kinh doanh.

Khi người dùng chào hỏi hoặc trò chuyện thông thường, hãy:
- Trả lời thân thiện bằng tiếng Việt
- Giới thiệu khả năng phân tích dữ liệu nếu phù hợp
- Hướng dẫn cách đặt câu hỏi về dữ liệu

Khả năng của bạn:
- Trả lời câu hỏi về doanh thu, đơn hàng, sản phẩm
- So sánh metrics giữa các periods
- Tìm top sản phẩm, top khách hàng
- Phân tích theo platform (Shopee, Lazada, etc.)

Ví dụ câu hỏi bạn có thể trả lời:
- "Tổng doanh thu tháng này là bao nhiêu?"
- "Top 5 sản phẩm bán chạy nhất?"
- "So sánh doanh thu tuần này với tuần trước"
"""
```

### Response Formatter Prompt (`app/prompts/system/response_formatter.py`)

```python
RESPONSE_FORMATTER_PROMPT = """Format kết quả phân tích dữ liệu cho người dùng.

Quy tắc format:
1. Trả lời bằng tiếng Việt
2. Format số tiền: 1.000.000 VND (dùng dấu chấm phân cách hàng nghìn)
3. Format phần trăm: 15,5% (dùng dấu phẩy cho số thập phân)
4. Nếu có nhiều items, dùng danh sách có đánh số
5. Nếu không có dữ liệu, thông báo rõ ràng
6. Giữ câu trả lời ngắn gọn, dễ hiểu

Ví dụ format tốt:
- "Tổng doanh thu tháng 1/2024: 150.000.000 VND"
- "Top 3 sản phẩm bán chạy:
   1. Áo thun - 500 đơn
   2. Quần jean - 350 đơn
   3. Giày sneaker - 200 đơn"
- "Doanh thu tuần này tăng 15,5% so với tuần trước (từ 50.000.000 lên 57.750.000 VND)"
"""
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Intent Classification Completeness

*For any* user message, the Intent_Classifier SHALL return exactly one of: "data_query", "chat", or "unclear".

**Validates: Requirements 1.1**

### Property 2: Workflow Routing Correctness

*For any* classified intent, the Chat_Workflow SHALL route to the correct node (data_agent_node for "data_query", chat_node for "chat", clarify_node for "unclear").

**Validates: Requirements 1.2, 1.3, 1.4**

### Property 3: Data Isolation

*For any* data query, all returned results SHALL only contain data from connections where connection.user_id equals the requesting user's ID.

**Validates: Requirements 12.1, 12.2, 12.3**

### Property 4: Pipeline Validation Security

*For any* execute_aggregation call, the pipeline SHALL NOT contain blocked stages ($out, $merge, $delete), and all $lookup targets SHALL belong to the user.

**Validates: Requirements 8.5, 8.6**

### Property 5: Result Limit Enforcement

*For any* execute_aggregation call, the returned results SHALL contain at most 1000 rows.

**Validates: Requirements 8.7**

### Property 6: Aggregation Operation Validity

*For any* aggregate_data call with operation O, O SHALL be one of: "sum", "count", "avg", "min", "max".

**Validates: Requirements 5.1**

### Property 7: Period Comparison Calculation

*For any* compare_periods call, the result SHALL include period1_value, period2_value, difference, and percentage_change where percentage_change = (period2 - period1) / period1 * 100.

**Validates: Requirements 7.2, 7.3**

### Property 8: Response Formatter Output

*For any* workflow execution that completes without error, the final_response field SHALL be non-empty.

**Validates: Requirements 9.1**

### Property 9: Conversation Context Preservation

*For any* workflow execution, the messages passed to nodes SHALL include the full conversation history from conversation_repo.

**Validates: Requirements 10.1, 10.2, 10.3**

### Property 10: Streaming Event Completeness

*For any* workflow execution, exactly one terminal event SHALL be emitted: either "chat:message:completed" or "chat:message:failed".

**Validates: Requirements 11.5, 11.6**

## Error Handling

### Tool Errors

| Error | Handling |
|-------|----------|
| Invalid connection_name | Return error message, agent retries with correct name |
| Invalid field name | Return error message, agent retries |
| Pipeline validation failed | Return validation error, agent corrects pipeline |
| Query execution failed | Return error, agent retries (max 3 times) |

### Workflow Errors

| Error | Handling |
|-------|----------|
| Intent classification failed | Default to "unclear" |
| Data agent max retries exceeded | Return user-friendly error message |
| No user connections | Return message to set up data sync |

### Socket Events

| Event | When |
|-------|------|
| chat:message:started | Workflow starts |
| chat:message:token | Token streamed |
| chat:message:tool_start | Tool execution starts |
| chat:message:tool_end | Tool execution ends |
| chat:message:completed | Workflow completes successfully |
| chat:message:failed | Workflow fails |

## Testing Strategy

### Unit Tests

- Intent classifier with various message types
- Pipeline validator with valid/invalid pipelines
- Aggregation operations (sum, count, avg, min, max)
- Number formatting (Vietnamese locale)

### Property-Based Tests

Property-based tests verify universal properties using `hypothesis`:

- Each property from Correctness Properties section
- Minimum 100 iterations per test
- Tag format: `# Feature: ai-chat-agent, Property N: {property_text}`

### Integration Tests

- Full workflow execution with mock LLM
- Tool execution with test database
- Socket event emission verification

## Folder Structure

```
app/
├── agents/
│   ├── __init__.py
│   ├── registry.py                    # (update)
│   └── implementations/
│       └── data_agent/                # NEW
│           ├── __init__.py
│           ├── agent.py
│           └── tools.py
│
├── graphs/
│   ├── __init__.py
│   ├── registry.py                    # NEW
│   ├── base/
│   │   ├── __init__.py
│   │   └── state.py
│   └── workflows/
│       └── chat_workflow/             # NEW
│           ├── __init__.py
│           ├── graph.py
│           ├── state.py
│           └── nodes/
│               ├── __init__.py
│               ├── intent_classifier.py
│               ├── chat_node.py
│               ├── data_agent_node.py
│               ├── clarify_node.py
│               └── response_formatter.py
│
├── prompts/
│   ├── __init__.py
│   └── system/
│       ├── __init__.py
│       ├── intent_classifier.py       # NEW
│       ├── data_agent.py              # NEW
│       ├── chat_node.py               # NEW
│       └── response_formatter.py      # NEW
│
├── services/
│   └── ai/
│       ├── __init__.py
│       ├── chat_service.py            # (update)
│       ├── conversation_service.py    # (existing)
│       ├── data_query_service.py      # NEW
│       └── pipeline_validator.py      # NEW
│
└── common/
    └── service.py                     # (update)
```
