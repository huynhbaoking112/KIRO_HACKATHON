# Requirements Document

## Introduction

Tích hợp khả năng Web Search vào hệ thống AI Chat thông qua DuckDuckGo MCP Server và langchain-mcp-adapters. Feature này cho phép cả chat_node và data_agent có thể search web và lấy content từ URLs để trả lời các câu hỏi cần thông tin từ internet.

## Glossary

- **MCP_Client**: MultiServerMCPClient từ langchain-mcp-adapters, quản lý connections đến MCP servers
- **MCP_Server**: External process cung cấp tools theo Model Context Protocol
- **DuckDuckGo_MCP**: MCP server cung cấp web search và content fetching tools
- **Web_Search_Tool**: Tool search web, trả về titles, URLs, snippets
- **Fetch_Content_Tool**: Tool lấy full text content từ một URL
- **Data_Agent**: ReAct agent xử lý data queries với tools
- **Chat_Agent**: Agent xử lý general conversation (upgraded từ chat_node)
- **MCP_Tools_Manager**: Component quản lý và cung cấp MCP tools cho agents

## Requirements

### Requirement 1: MCP Infrastructure Setup

**User Story:** As a developer, I want to have a centralized MCP client manager, so that all agents can access MCP tools consistently.

#### Acceptance Criteria

1. THE MCP_Tools_Manager SHALL initialize MultiServerMCPClient with configured MCP servers on application startup
2. THE MCP_Tools_Manager SHALL provide a singleton instance accessible throughout the application
3. WHEN MCP_Tools_Manager initializes, THE System SHALL load tools from all configured MCP servers
4. IF MCP server connection fails, THEN THE System SHALL log the error and continue without those tools
5. THE MCP_Tools_Manager SHALL support adding multiple MCP servers via configuration

### Requirement 2: DuckDuckGo MCP Server Integration

**User Story:** As a developer, I want to integrate DuckDuckGo MCP Server, so that agents can search the web.

#### Acceptance Criteria

1. THE System SHALL configure DuckDuckGo MCP Server using stdio transport
2. WHEN DuckDuckGo MCP Server is configured, THE MCP_Client SHALL spawn it as a subprocess
3. THE System SHALL expose two tools from DuckDuckGo MCP: search and fetch_content
4. THE Web_Search_Tool SHALL accept query string and max_results parameters
5. THE Fetch_Content_Tool SHALL accept URL parameter and return cleaned text content

### Requirement 3: Data Agent Web Search Integration

**User Story:** As a user, I want the data agent to search the web when my question requires external information, so that I can get answers about market prices, competitors, or trends.

#### Acceptance Criteria

1. WHEN Data_Agent is created, THE System SHALL include MCP web search tools alongside existing data tools
2. THE Data_Agent system prompt SHALL instruct when to use web search vs data tools
3. WHEN user asks about external information (prices, news, competitors), THE Data_Agent SHALL use Web_Search_Tool
4. WHEN Data_Agent needs detailed information from a URL, THE Data_Agent SHALL use Fetch_Content_Tool
5. THE Data_Agent SHALL format web search results in Vietnamese with proper formatting

### Requirement 4: Chat Agent Web Search Integration

**User Story:** As a user, I want the chat assistant to search the web when I ask general questions, so that I can get up-to-date information.

#### Acceptance Criteria

1. THE Chat_Node SHALL be upgraded to Chat_Agent with tool calling capability
2. WHEN Chat_Agent is created, THE System SHALL include MCP web search tools
3. THE Chat_Agent system prompt SHALL instruct when to use web search for general questions
4. WHEN user asks questions requiring current information, THE Chat_Agent SHALL use Web_Search_Tool
5. THE Chat_Agent SHALL maintain streaming capability for responses
6. THE Chat_Agent SHALL emit tool call events via Socket.IO (tool_start, tool_end)

### Requirement 5: Configuration Management

**User Story:** As a developer, I want MCP servers to be configurable, so that I can easily add or modify MCP integrations.

#### Acceptance Criteria

1. THE System SHALL store MCP server configurations in a dedicated config module
2. THE Configuration SHALL support stdio transport with command and args
3. THE Configuration SHALL support HTTP transport with URL (for future use)
4. WHEN configuration changes, THE System SHALL be able to reload MCP connections without restart
5. THE Configuration SHALL allow enabling/disabling individual MCP servers

### Requirement 6: Error Handling and Resilience

**User Story:** As a user, I want the system to handle web search failures gracefully, so that I still get useful responses.

#### Acceptance Criteria

1. IF Web_Search_Tool fails, THEN THE Agent SHALL inform user and suggest alternatives
2. IF Fetch_Content_Tool fails for a URL, THEN THE Agent SHALL try other URLs from search results
3. IF MCP server becomes unavailable, THEN THE System SHALL continue with remaining tools
4. THE System SHALL implement timeout for web search operations (max 30 seconds)
5. IF search returns no results, THEN THE Agent SHALL inform user clearly in Vietnamese
