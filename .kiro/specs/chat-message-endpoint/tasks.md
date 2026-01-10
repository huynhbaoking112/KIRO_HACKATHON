# Implementation Plan: Chat Message Endpoint

## Overview

Implement endpoint cho phép user gửi message và nhận AI response qua Socket.IO streaming. Sử dụng FastAPI BackgroundTasks, LangGraph ReAct agent với OpenAI, và tích hợp với ConversationService đã có.

## Tasks

- [x] 1. Setup Infrastructure
  - [x] 1.1 Add dependencies to requirements.txt
    - Add `langchain-openai` và `langgraph`
    - _Requirements: 3.1, 4.1_
  - [x] 1.2 Create LLM Factory `app/infrastructure/llm/factory.py`
    - Implement get_chat_openai() function
    - Use OPENAI_API_KEY from settings
    - Enable streaming by default
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 2. Implement Socket Events và Schemas
  - [x] 2.1 Update `app/common/event_socket.py`
    - Add ChatEvents class với 6 event constants
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  - [x] 2.2 Create `app/domain/schemas/chat.py`
    - Implement SendMessageRequest schema
    - Implement SendMessageResponse schema
    - Implement socket payload schemas (optional, for documentation)
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 3. Implement Default Agent
  - [ ] 3.1 Create `app/agents/implementations/default_agent/__init__.py`
    - Empty init file for package
  - [ ] 3.2 Create `app/agents/implementations/default_agent/tools.py`
    - Implement calculator tool with safe expression evaluation
    - Only allow digits and basic operators
    - Return error message for invalid expressions
    - _Requirements: 3.4, 3.5_
  - [ ] 3.3 Create `app/agents/implementations/default_agent/agent.py`
    - Implement create_default_agent() function
    - Use LangGraph create_react_agent
    - Include calculator tool
    - Configure system prompt
    - _Requirements: 3.1, 3.2, 3.3_
  - [ ] 3.4 Update `app/agents/registry.py`
    - Implement get_default_agent() with lru_cache
    - _Requirements: 5.1, 5.2_

- [ ] 4. Checkpoint - Verify Agent Setup
  - Ensure agent can be created and has calculator tool
  - Test calculator tool with sample expressions

- [ ] 5. Implement Chat Service
  - [ ] 5.1 Update `app/services/ai/chat_service.py`
    - Implement ChatService class
    - Inject ConversationService dependency
    - Implement send_message() method
    - _Requirements: 1.2, 1.3, 1.4_
  - [ ] 5.2 Implement process_agent_response() method
    - Load conversation history as LangChain messages
    - Emit MESSAGE_STARTED event
    - Call agent.astream_events() with version="v2"
    - Handle on_chat_model_stream → emit MESSAGE_TOKEN
    - Handle on_tool_start → emit MESSAGE_TOOL_START
    - Handle on_tool_end → emit MESSAGE_TOOL_END
    - Save assistant message to database
    - Emit MESSAGE_COMPLETED event
    - Handle errors → emit MESSAGE_FAILED
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 6.7_
  - [ ] 5.3 Add get_chat_service() to `app/common/service.py`
    - Create factory function with lru_cache
    - _Requirements: 5.1_

- [ ] 6. Implement Chat API Endpoint
  - [ ] 6.1 Create `app/api/v1/ai/chat.py`
    - Create router with prefix="/chat"
    - Implement POST /messages endpoint
    - Validate request
    - Handle conversation creation if needed
    - Save user message
    - Add background task
    - Return SendMessageResponse
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_
  - [ ] 6.2 Register router in `app/api/v1/__init__.py` or main router
    - Include chat router in API v1
    - _Requirements: 1.1_

- [ ] 7. Final Checkpoint - Integration Test
  - Test full flow: POST message → Socket events → DB persistence
  - Test conversation creation flow
  - Test calculator tool invocation
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Sử dụng ConversationService đã implement từ conversation-storage spec
- Socket.IO server đã có sẵn tại `app/socket_gateway/server.py`
- User authentication đã có sẵn via `get_current_user` dependency
- BackgroundTasks là FastAPI built-in, không cần Redis queue
