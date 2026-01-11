# Requirements Document

## Introduction

Endpoint cho phép user gửi message đến AI agent và nhận response qua Socket.IO streaming. Hệ thống sử dụng FastAPI BackgroundTasks để xử lý async, LangGraph ReAct agent với tool calling, và Socket.IO để stream response realtime về client.

## Glossary

- **Chat_Service**: Business logic layer xử lý chat messages và orchestrate agent
- **Chat_API**: REST endpoint nhận message từ user
- **Default_Agent**: LangGraph ReAct agent với calculator tool
- **Agent_Registry**: Factory pattern để lấy agent instances
- **LLM_Factory**: Factory để tạo OpenAI ChatModel instances
- **Calculator_Tool**: Tool đơn giản để tính toán biểu thức toán học
- **BackgroundTasks**: FastAPI built-in mechanism để chạy tasks sau khi response

## Requirements

### Requirement 1: Chat API Endpoint

**User Story:** As a user, I want to send a message via REST API, so that I can start a conversation with the AI agent.

#### Acceptance Criteria

1. THE Chat_API SHALL accept POST requests to `/api/v1/ai/chat/messages` with content field
2. WHEN conversation_id is not provided, THE Chat_API SHALL create a new conversation
3. WHEN conversation_id is provided, THE Chat_API SHALL use the existing conversation
4. THE Chat_API SHALL save the user message to database before returning response
5. THE Chat_API SHALL add a background task to process agent response
6. THE Chat_API SHALL return user_message_id and conversation_id immediately
7. IF conversation_id is invalid or not found, THEN THE Chat_API SHALL return 404 error

### Requirement 2: Agent Response Processing

**User Story:** As a user, I want the AI to process my message and stream the response, so that I can see the answer in realtime.

#### Acceptance Criteria

1. THE Chat_Service SHALL load conversation history as LangChain messages before calling agent
2. THE Chat_Service SHALL emit `chat:message:started` event when processing begins
3. THE Chat_Service SHALL stream tokens via `chat:message:token` events as they are generated
4. WHEN agent calls a tool, THE Chat_Service SHALL emit `chat:message:tool_start` event
5. WHEN tool execution completes, THE Chat_Service SHALL emit `chat:message:tool_end` event
6. THE Chat_Service SHALL save assistant message to database when streaming completes
7. THE Chat_Service SHALL emit `chat:message:completed` event with full content and message_id
8. IF an error occurs during processing, THEN THE Chat_Service SHALL emit `chat:message:failed` event

### Requirement 3: Default Agent

**User Story:** As a developer, I want a default AI agent with basic tool, so that users can interact with AI immediately.

#### Acceptance Criteria

1. THE Default_Agent SHALL be a LangGraph ReAct agent using OpenAI model
2. THE Default_Agent SHALL have a calculator tool for mathematical expressions
3. THE Default_Agent SHALL support streaming via astream_events
4. THE Calculator_Tool SHALL evaluate basic mathematical expressions safely
5. IF calculator receives invalid expression, THEN THE Calculator_Tool SHALL return error message

### Requirement 4: LLM Infrastructure

**User Story:** As a developer, I want a factory to create LLM instances, so that I can easily configure and swap models.

#### Acceptance Criteria

1. THE LLM_Factory SHALL create ChatOpenAI instances with configurable parameters
2. THE LLM_Factory SHALL use OPENAI_API_KEY from settings
3. THE LLM_Factory SHALL enable streaming by default

### Requirement 5: Agent Registry

**User Story:** As a developer, I want a registry to manage agent instances, so that I can easily get and reuse agents.

#### Acceptance Criteria

1. THE Agent_Registry SHALL provide get_default_agent() function
2. THE Agent_Registry SHALL return singleton agent instance using lru_cache

### Requirement 6: Socket Events

**User Story:** As a developer, I want well-defined socket events, so that clients can handle responses consistently.

#### Acceptance Criteria

1. THE ChatEvents SHALL define MESSAGE_STARTED event as "chat:message:started"
2. THE ChatEvents SHALL define MESSAGE_TOKEN event as "chat:message:token"
3. THE ChatEvents SHALL define MESSAGE_TOOL_START event as "chat:message:tool_start"
4. THE ChatEvents SHALL define MESSAGE_TOOL_END event as "chat:message:tool_end"
5. THE ChatEvents SHALL define MESSAGE_COMPLETED event as "chat:message:completed"
6. THE ChatEvents SHALL define MESSAGE_FAILED event as "chat:message:failed"
7. ALL socket events SHALL be emitted to room "user:{user_id}"

### Requirement 7: Request/Response Schemas

**User Story:** As a developer, I want Pydantic schemas for validation, so that I have type safety.

#### Acceptance Criteria

1. THE SendMessageRequest SHALL have optional conversation_id field
2. THE SendMessageRequest SHALL have required content field with min_length=1
3. THE SendMessageResponse SHALL have user_message_id and conversation_id fields
4. THE MessageCompletedPayload SHALL have conversation_id, message_id, content, and optional metadata
