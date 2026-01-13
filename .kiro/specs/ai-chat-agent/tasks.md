# Implementation Plan: AI Chat Agent

## Overview

Triển khai AI Chat Agent sử dụng LangGraph workflow với multi-node architecture. Implementation theo thứ tự: infrastructure → services → tools → nodes → graph → integration.

## Tasks

- [x] 1. Set up project structure and base components
  - [x] 1.1 Create graph base structure
    - Create `app/graphs/__init__.py`, `app/graphs/registry.py`
    - Create `app/graphs/base/__init__.py`, `app/graphs/base/state.py`
    - _Requirements: 14.1_

  - [x] 1.2 Create prompt templates
    - Create `app/prompts/system/__init__.py`
    - Create `app/prompts/system/intent_classifier.py` with INTENT_CLASSIFIER_PROMPT
    - Create `app/prompts/system/data_agent.py` with DATA_AGENT_SYSTEM_PROMPT
    - Create `app/prompts/system/chat_node.py` with CHAT_NODE_PROMPT
    - Create `app/prompts/system/response_formatter.py` with RESPONSE_FORMATTER_PROMPT
    - _Requirements: 1.5, 2.2, 3.2, 9.2, 9.3, 9.4_

- [x] 2. Implement Service Layer
  - [x] 2.1 Create PipelineValidator service
    - Create `app/services/ai/pipeline_validator.py`
    - Implement ALLOWED_STAGES, BLOCKED_STAGES constants
    - Implement `validate()` method to check pipeline stages
    - Implement connection_id ownership verification for $lookup
    - Implement MAX_LIMIT enforcement
    - _Requirements: 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

  - [ ]* 2.2 Write property tests for PipelineValidator
    - **Property 4: Pipeline Validation Security**
    - **Property 5: Result Limit Enforcement**
    - **Validates: Requirements 8.5, 8.6, 8.7**

  - [x] 2.3 Create DataQueryService
    - Create `app/services/ai/data_query_service.py`
    - Implement `get_user_connections()` to fetch user's sheet connections with schemas
    - Implement `aggregate()` for sum/count/avg/min/max operations
    - Implement `get_top_items()` for top N queries
    - Implement `execute_pipeline()` for custom aggregation pipelines
    - _Requirements: 4.1, 4.2, 5.1, 5.2, 6.1, 6.2, 8.1_

  - [ ]* 2.4 Write property tests for DataQueryService
    - **Property 3: Data Isolation**
    - **Property 6: Aggregation Operation Validity**
    - **Validates: Requirements 5.1, 12.1, 12.2, 12.3**

- [ ] 3. Checkpoint - Ensure service layer tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement Data Agent Tools
  - [x] 4.1 Create get_data_schema tool
    - Create `app/agents/implementations/data_agent/__init__.py`
    - Create `app/agents/implementations/data_agent/tools.py`
    - Implement `create_get_data_schema_tool()` factory function
    - Return connection names, field names, data types, sample values
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 4.2 Create aggregate_data tool
    - Implement `create_aggregate_data_tool()` factory function
    - Support operations: sum, count, avg, min, max
    - Support filters, group_by, date_field, date_from, date_to parameters
    - Return results as JSON string
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 4.3 Create get_top_items tool
    - Implement `create_get_top_items_tool()` factory function
    - Support sort_field, sort_order, limit, group_by, aggregate_field, filters
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 4.4 Create compare_periods tool
    - Implement `create_compare_periods_tool()` factory function
    - Calculate period1_value, period2_value, difference, percentage_change
    - Support sum, count, avg operations
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ]* 4.5 Write property test for compare_periods
    - **Property 7: Period Comparison Calculation**
    - **Validates: Requirements 7.2, 7.3**

  - [x] 4.6 Create execute_aggregation tool
    - Implement `create_execute_aggregation_tool()` factory function
    - Integrate PipelineValidator for validation
    - Execute validated pipeline via DataQueryService
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 5. Implement Data Agent
  - [x] 5.1 Create Data Agent
    - Create `app/agents/implementations/data_agent/agent.py`
    - Implement `create_data_agent()` function using `create_react_agent`
    - Bind all 5 tools to agent
    - Format schema_context in system prompt
    - _Requirements: 4.1, 5.1, 6.1, 7.1, 8.1_

  - [x] 5.2 Update agent registry
    - Update `app/agents/registry.py` to register data_agent
    - _Requirements: 14.1_

- [ ] 6. Checkpoint - Ensure agent and tools tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement Workflow Nodes
  - [x] 7.1 Create ChatWorkflowState
    - Create `app/graphs/workflows/chat_workflow/__init__.py`
    - Create `app/graphs/workflows/chat_workflow/state.py`
    - Define ChatWorkflowState TypedDict with all required fields
    - _Requirements: 14.1_

  - [x] 7.2 Create intent_classifier node
    - Create `app/graphs/workflows/chat_workflow/nodes/__init__.py`
    - Create `app/graphs/workflows/chat_workflow/nodes/intent_classifier.py`
    - Implement `intent_classifier_node()` using LLM with INTENT_CLASSIFIER_PROMPT
    - Return {"intent": "data_query" | "chat" | "unclear"}
    - _Requirements: 1.1, 1.5_

  - [ ]* 7.3 Write property test for intent_classifier
    - **Property 1: Intent Classification Completeness**
    - **Validates: Requirements 1.1**

  - [x] 7.4 Create chat_node
    - Create `app/graphs/workflows/chat_workflow/nodes/chat_node.py`
    - Implement `chat_node()` using LLM with CHAT_NODE_PROMPT
    - Return {"agent_response": str}
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 7.5 Create clarify_node
    - Create `app/graphs/workflows/chat_workflow/nodes/clarify_node.py`
    - Implement `clarify_node()` using LLM
    - Provide examples of supported queries
    - Return {"agent_response": str}
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 7.6 Create data_agent_node
    - Create `app/graphs/workflows/chat_workflow/nodes/data_agent_node.py`
    - Implement `data_agent_node()` that invokes Data Agent
    - Capture tool_calls for streaming
    - Handle retries (max 3 times)
    - Return {"agent_response": str, "tool_calls": list}
    - _Requirements: 13.1, 13.2_

  - [x] 7.7 Create response_formatter node
    - Create `app/graphs/workflows/chat_workflow/nodes/response_formatter.py`
    - Implement `response_formatter_node()` using LLM with RESPONSE_FORMATTER_PROMPT
    - Format numbers with Vietnamese locale (1.000.000 VND)
    - Return {"final_response": str}
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 7.8 Write property test for response_formatter
    - **Property 8: Response Formatter Output**
    - **Validates: Requirements 9.1**

- [ ] 8. Implement Chat Workflow Graph
  - [ ] 8.1 Create ChatWorkflow graph
    - Create `app/graphs/workflows/chat_workflow/graph.py`
    - Implement ChatWorkflow class with StateGraph
    - Add all 5 nodes to graph
    - Implement `route_by_intent()` conditional routing function
    - Add conditional edges from intent_classifier to handler nodes
    - Add edges from handler nodes to response_formatter
    - Add edge from response_formatter to END
    - _Requirements: 14.1, 14.2, 14.3, 14.4_

  - [ ]* 8.2 Write property test for workflow routing
    - **Property 2: Workflow Routing Correctness**
    - **Validates: Requirements 1.2, 1.3, 1.4**

  - [ ] 8.3 Update graph registry
    - Create/update `app/graphs/registry.py` to register chat_workflow
    - _Requirements: 14.1_

- [ ] 9. Checkpoint - Ensure workflow tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Integrate with Chat Service
  - [ ] 10.1 Update ChatService
    - Update `app/services/ai/chat_service.py`
    - Add DataQueryService dependency
    - Implement `process_message()` using ChatWorkflow
    - Load user_connections and conversation history
    - Stream workflow execution via `astream_events`
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [ ]* 10.2 Write property test for conversation context
    - **Property 9: Conversation Context Preservation**
    - **Validates: Requirements 10.1, 10.2, 10.3**

  - [ ] 10.3 Implement Socket.IO streaming
    - Emit "chat:message:started" when workflow starts
    - Emit "chat:message:token" for streamed tokens
    - Emit "chat:message:tool_start" and "chat:message:tool_end" for tool calls
    - Emit "chat:message:completed" on success
    - Emit "chat:message:failed" on error
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

  - [ ]* 10.4 Write property test for streaming events
    - **Property 10: Streaming Event Completeness**
    - **Validates: Requirements 11.5, 11.6**

- [ ] 11. Update Common Service Factory
  - [ ] 11.1 Update service factory
    - Update `app/common/service.py`
    - Add `get_data_query_service()` factory function
    - Add `get_pipeline_validator()` factory function
    - Update `get_chat_service()` to include new dependencies
    - _Requirements: 14.1_

- [ ] 12. Error Handling Implementation
  - [ ] 12.1 Implement error handling
    - Handle no user connections case with friendly message
    - Implement retry logic in data_agent_node (max 3 retries)
    - Log errors for debugging
    - Return user-friendly Vietnamese error messages
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [ ] 13. Final Checkpoint - Full integration test
  - Ensure all tests pass, ask the user if questions arise.
  - Verify end-to-end workflow execution
  - Verify Socket.IO event emission

## Notes

- Tasks marked with `*` are optional property-based tests
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests use `hypothesis` library with minimum 100 iterations
- All responses must be in Vietnamese with Vietnamese number formatting
