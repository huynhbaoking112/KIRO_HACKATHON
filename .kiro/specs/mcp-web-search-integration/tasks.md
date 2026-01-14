# Implementation Plan: MCP Web Search Integration

## Overview

Tích hợp DuckDuckGo MCP Server vào hệ thống AI Chat thông qua langchain-mcp-adapters. Implementation theo thứ tự: infrastructure → agents → integration → testing.

## Tasks

- [x] 1. Setup dependencies và configuration
  - [x] 1.1 Add dependencies to requirements.txt
    - Add `langchain-mcp-adapters>=0.1.0`
    - Add `duckduckgo-mcp-server>=0.1.0`
    - _Requirements: 2.1_

  - [x] 1.2 Create MCP configuration module
    - Create `app/config/mcp.py`
    - Define MCPServerConfig TypedDict
    - Configure DuckDuckGo MCP server with stdio transport
    - Support enabled/disabled flag per server
    - _Requirements: 5.1, 5.2, 5.3, 5.5_

- [x] 2. Implement MCP Tools Manager
  - [x] 2.1 Create MCP infrastructure module structure
    - Create `app/infrastructure/mcp/__init__.py`
    - Create `app/infrastructure/mcp/manager.py`
    - _Requirements: 1.1_

  - [x] 2.2 Implement MCPToolsManager class
    - Implement singleton pattern with get_instance()
    - Implement initialize() method with MultiServerMCPClient
    - Implement get_tools() method
    - Implement reload() method for config changes
    - Filter disabled servers from initialization
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 5.4, 5.5_

  - [x] 2.3 Add error handling for MCP initialization
    - Catch connection failures and log errors
    - Continue with empty tools if MCP fails
    - Implement 30 second timeout
    - _Requirements: 1.4, 6.3, 6.4_

  - [ ]* 2.4 Write property test for singleton consistency
    - **Property 2: Singleton Consistency**
    - **Validates: Requirements 1.2**

  - [ ]* 2.5 Write property test for disabled server exclusion
    - **Property 5: Disabled Server Exclusion**
    - **Validates: Requirements 5.5**

- [ ] 3. Checkpoint - Verify MCP infrastructure
  - Ensure MCP manager initializes correctly
  - Verify tools are loaded from DuckDuckGo MCP
  - Ask the user if questions arise

- [x] 4. Update Data Agent with MCP tools
  - [x] 4.1 Update data_agent.py to include MCP tools
    - Import MCPToolsManager
    - Get MCP tools and combine with existing data tools
    - Pass combined tools to create_react_agent
    - _Requirements: 3.1_

  - [x] 4.2 Update DATA_AGENT_SYSTEM_PROMPT
    - Create new prompt in `app/prompts/system/data_agent.py`
    - Add instructions for when to use web search
    - Explain web_search and fetch_content tools
    - _Requirements: 3.2, 3.3, 3.4, 3.5_

  - [ ]* 4.3 Write property test for agent tool inclusion (data_agent)
    - **Property 3: Agent Tool Inclusion**
    - **Validates: Requirements 3.1**

- [x] 5. Create Chat Agent with MCP tools
  - [x] 5.1 Create chat_agent module structure
    - Create `app/agents/implementations/chat_agent/__init__.py`
    - Create `app/agents/implementations/chat_agent/agent.py`
    - _Requirements: 4.1_

  - [x] 5.2 Implement create_chat_agent function
    - Create ReAct agent with MCP tools
    - Configure LLM with temperature=0.7, streaming=True
    - _Requirements: 4.1, 4.2_

  - [x] 5.3 Create CHAT_AGENT_SYSTEM_PROMPT
    - Create `app/prompts/system/chat_agent.py`
    - Instructions for friendly Vietnamese responses
    - When to use web search for current information
    - _Requirements: 4.3, 4.4_

  - [ ]* 5.4 Write property test for agent tool inclusion (chat_agent)
    - **Property 3: Agent Tool Inclusion**
    - **Validates: Requirements 4.2**

- [x] 6. Update chat_node to use chat_agent
  - [x] 6.1 Refactor chat_node.py
    - Import create_chat_agent
    - Replace direct LLM call with agent execution
    - Maintain streaming capability
    - _Requirements: 4.1, 4.5_

  - [x] 6.2 Implement tool event streaming
    - Emit ChatEvents.MESSAGE_TOOL_START before tool execution
    - Emit ChatEvents.MESSAGE_TOOL_END after tool execution
    - Include tool name and arguments in events
    - _Requirements: 4.6_

  - [ ]* 6.3 Write property test for tool event emission
    - **Property 4: Tool Event Emission**
    - **Validates: Requirements 4.6**

- [ ] 7. Checkpoint - Verify agent integration
  - Test data_agent with web search query
  - Test chat_agent with web search query
  - Verify Socket.IO events are emitted
  - Ask the user if questions arise

- [ ] 8. Application startup integration
  - [ ] 8.1 Initialize MCP manager on app startup
    - Update `app/main.py` or startup hook
    - Call MCPToolsManager.initialize() with config
    - Handle initialization errors gracefully
    - _Requirements: 1.1, 1.4_

  - [ ]* 8.2 Write property test for MCP initialization completeness
    - **Property 1: MCP Initialization Completeness**
    - **Validates: Requirements 1.1, 1.3, 1.5**

- [ ] 9. Error handling and resilience
  - [ ] 9.1 Implement graceful degradation
    - Agents work without MCP tools if unavailable
    - Log warnings when MCP tools missing
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ] 9.2 Add user-friendly error messages
    - Vietnamese error messages for search failures
    - Suggest alternatives when search fails
    - _Requirements: 6.1, 6.5_

- [ ] 10. Final checkpoint - End-to-end testing
  - Test complete flow: user question → web search → response
  - Verify error handling works correctly
  - Ensure all tests pass
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional property-based tests
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
