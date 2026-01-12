# Requirements Document

## Introduction

AI Chat Agent cho phép người dùng query và phân tích dữ liệu kinh doanh bằng ngôn ngữ tự nhiên (tiếng Việt). Hệ thống sử dụng LangGraph workflow với multi-node architecture để phân loại intent và route đến agent phù hợp. Data Agent sử dụng ReAct pattern với custom tools để query MongoDB aggregation pipelines.

## Glossary

- **Chat_Workflow**: LangGraph workflow chính điều phối toàn bộ luồng xử lý chat
- **Intent_Classifier**: Node phân loại ý định người dùng (data_query, chat, unclear)
- **Data_Agent**: ReAct agent với tools để query dữ liệu từ MongoDB
- **Chat_Node**: Node xử lý các câu hỏi chit-chat thông thường
- **Clarify_Node**: Node yêu cầu người dùng làm rõ câu hỏi
- **Response_Formatter**: Node format kết quả cuối cùng cho người dùng
- **Sheet_Connection**: Cấu hình kết nối Google Sheet của user (từ feature google-sheet-crawler)
- **Aggregation_Pipeline**: MongoDB aggregation pipeline để query dữ liệu
- **Tool**: Function mà Data_Agent có thể gọi để thực hiện query

## Requirements

### Requirement 1: Intent Classification

**User Story:** As a user, I want the system to understand my intent, so that my question is routed to the appropriate handler.

#### Acceptance Criteria

1. WHEN a user sends a message, THE Intent_Classifier SHALL classify it into one of: "data_query", "chat", or "unclear"
2. WHEN the intent is "data_query", THE Chat_Workflow SHALL route to Data_Agent node
3. WHEN the intent is "chat", THE Chat_Workflow SHALL route to Chat_Node
4. WHEN the intent is "unclear", THE Chat_Workflow SHALL route to Clarify_Node
5. THE Intent_Classifier SHALL use LLM to perform classification with conversation context

### Requirement 2: Chat Node (General Conversation)

**User Story:** As a user, I want to have general conversations with the assistant, so that I can get help beyond data queries.

#### Acceptance Criteria

1. WHEN routed to Chat_Node, THE System SHALL respond to general questions, greetings, and chitchat
2. WHEN responding, THE Chat_Node SHALL maintain a friendly, helpful tone in Vietnamese
3. WHEN the user asks about capabilities, THE Chat_Node SHALL explain what data queries are supported

### Requirement 3: Clarify Node

**User Story:** As a user, I want the system to ask for clarification when my question is unclear, so that I can provide more context.

#### Acceptance Criteria

1. WHEN routed to Clarify_Node, THE System SHALL ask the user to clarify their question
2. WHEN asking for clarification, THE Clarify_Node SHALL provide examples of supported queries
3. THE Clarify_Node SHALL respond in Vietnamese

### Requirement 4: Data Agent Tools - Schema Discovery

**User Story:** As a user, I want the agent to know my data structure, so that it can query my data correctly.

#### Acceptance Criteria

1. THE Data_Agent SHALL have a get_data_schema tool to list user's connections and their fields
2. WHEN get_data_schema is called without parameters, THE Tool SHALL return all connections belonging to the user
3. WHEN get_data_schema is called with connection_name, THE Tool SHALL return detailed field information for that connection
4. THE get_data_schema tool SHALL return field names, data types, and sample values

### Requirement 5: Data Agent Tools - Simple Aggregation

**User Story:** As a user, I want to perform simple aggregations on my data, so that I can get quick insights.

#### Acceptance Criteria

1. THE Data_Agent SHALL have an aggregate_data tool for sum, count, avg, min, max operations
2. WHEN aggregate_data is called, THE Tool SHALL filter data by the user's connection_id
3. WHEN aggregate_data includes date filters, THE Tool SHALL apply date range filtering
4. WHEN aggregate_data includes group_by, THE Tool SHALL group results by the specified field
5. THE aggregate_data tool SHALL return results as JSON string

### Requirement 6: Data Agent Tools - Top Items

**User Story:** As a user, I want to find top items in my data, so that I can identify best performers.

#### Acceptance Criteria

1. THE Data_Agent SHALL have a get_top_items tool to retrieve top N items by a field
2. WHEN get_top_items is called, THE Tool SHALL sort and limit results
3. WHEN get_top_items includes group_by, THE Tool SHALL aggregate before sorting
4. THE get_top_items tool SHALL support both ascending and descending order

### Requirement 7: Data Agent Tools - Period Comparison

**User Story:** As a user, I want to compare metrics between time periods, so that I can track trends.

#### Acceptance Criteria

1. THE Data_Agent SHALL have a compare_periods tool to compare two time periods
2. WHEN compare_periods is called, THE Tool SHALL return values for both periods
3. THE compare_periods tool SHALL calculate difference and percentage change
4. THE compare_periods tool SHALL support sum, count, and avg operations

### Requirement 8: Data Agent Tools - Advanced Aggregation

**User Story:** As a user, I want to perform complex queries including joins, so that I can analyze data across multiple sheets.

#### Acceptance Criteria

1. THE Data_Agent SHALL have an execute_aggregation tool for custom MongoDB pipelines
2. WHEN execute_aggregation is called, THE Tool SHALL validate the pipeline before execution
3. THE execute_aggregation tool SHALL support $match, $group, $sort, $limit, $project stages
4. THE execute_aggregation tool SHALL support $lookup for joining connections
5. THE execute_aggregation tool SHALL block dangerous stages ($out, $merge, $delete)
6. THE execute_aggregation tool SHALL verify all connection_ids belong to the user
7. THE execute_aggregation tool SHALL limit results to maximum 1000 rows

### Requirement 9: Response Formatter

**User Story:** As a user, I want responses formatted nicely, so that I can easily understand the results.

#### Acceptance Criteria

1. WHEN Data_Agent completes, THE Response_Formatter SHALL format the final answer
2. THE Response_Formatter SHALL format numbers with Vietnamese locale (e.g., 1.000.000)
3. THE Response_Formatter SHALL format currency with VND suffix
4. THE Response_Formatter SHALL respond in Vietnamese
5. IF no data is found, THE Response_Formatter SHALL inform the user clearly

### Requirement 10: Conversation Memory

**User Story:** As a user, I want the system to remember our conversation, so that I can ask follow-up questions.

#### Acceptance Criteria

1. THE Chat_Workflow SHALL load conversation history from conversation_repo
2. THE Chat_Workflow SHALL pass conversation history to all nodes as context
3. WHEN processing a message, THE System SHALL consider previous messages for context
4. THE System SHALL save assistant responses to message_repo

### Requirement 11: Streaming Response

**User Story:** As a user, I want to see responses as they are generated, so that I don't have to wait for the full response.

#### Acceptance Criteria

1. THE Chat_Workflow SHALL stream tokens via Socket.IO events
2. WHEN a tool is called, THE System SHALL emit "chat:message:tool_start" event
3. WHEN a tool completes, THE System SHALL emit "chat:message:tool_end" event
4. WHEN streaming tokens, THE System SHALL emit "chat:message:token" event
5. WHEN response is complete, THE System SHALL emit "chat:message:completed" event
6. IF an error occurs, THE System SHALL emit "chat:message:failed" event

### Requirement 12: Data Isolation

**User Story:** As a user, I want my data to be private, so that other users cannot access it.

#### Acceptance Criteria

1. WHEN querying data, THE System SHALL filter by user's connection_ids only
2. WHEN using $lookup, THE System SHALL verify target connection belongs to user
3. THE System SHALL NOT expose data from other users' connections

### Requirement 13: Error Handling

**User Story:** As a user, I want helpful error messages, so that I can understand what went wrong.

#### Acceptance Criteria

1. IF a tool execution fails, THE Data_Agent SHALL retry with corrected parameters (max 3 times)
2. IF all retries fail, THE System SHALL return a user-friendly error message in Vietnamese
3. IF the user has no connections, THE System SHALL inform them to set up data sync first
4. THE System SHALL log errors for debugging purposes

### Requirement 14: Graph Workflow Structure

**User Story:** As a developer, I want a well-structured workflow, so that the system is maintainable.

#### Acceptance Criteria

1. THE Chat_Workflow SHALL be implemented as a LangGraph StateGraph
2. THE Chat_Workflow SHALL have nodes: intent_classifier, chat_node, data_agent_node, clarify_node, response_formatter
3. THE Chat_Workflow SHALL use conditional edges based on intent classification
4. ALL nodes SHALL output to response_formatter before END
