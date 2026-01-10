"""Chat service for handling chat messages and AI agent responses.

Provides business logic for:
- Sending user messages and creating conversations
- Processing agent responses with streaming via Socket.IO
- Managing conversation history for AI context
"""

import logging
from typing import Optional

from app.agents.registry import get_default_agent
from app.common.event_socket import ChatEvents
from app.domain.models.message import MessageMetadata, MessageRole
from app.services.ai.conversation_service import ConversationService
from app.socket_gateway import gateway

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat messages and AI agent responses.

    Handles:
    - Saving user messages to conversations
    - Creating new conversations when needed
    - Processing agent responses with streaming
    - Emitting socket events for real-time updates
    """

    def __init__(self, conversation_service: ConversationService):
        """Initialize ChatService with dependencies.

        Args:
            conversation_service: Service for conversation/message operations
        """
        self.conversation_service = conversation_service

    async def send_message(
        self,
        user_id: str,
        content: str,
        conversation_id: Optional[str] = None,
    ) -> tuple[str, str]:
        """Save user message and return message_id and conversation_id.

        If conversation_id is not provided, creates a new conversation.

        Args:
            user_id: ID of the user sending the message
            content: Message content text
            conversation_id: Optional existing conversation ID

        Returns:
            Tuple of (user_message_id, conversation_id)

        Requirements: 1.2, 1.3, 1.4
        """
        # Create new conversation if not provided
        if conversation_id is None:
            conversation = await self.conversation_service.create_conversation(
                user_id=user_id,
            )
            conversation_id = conversation.id

        # Save user message to database
        message = await self.conversation_service.add_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
        )

        return message.id, conversation_id

    async def process_agent_response(
        self,
        user_id: str,
        conversation_id: str,
    ) -> None:
        """Process agent response and stream via socket events.

        This method is designed to run as a background task.
        It loads conversation history, calls the agent with streaming,
        and emits socket events for each token/tool call.

        Args:
            user_id: ID of the user (for socket room targeting)
            conversation_id: ID of the conversation to process

        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 6.7
        """
        try:
            # Emit MESSAGE_STARTED event
            await gateway.emit_to_user(
                user_id=user_id,
                event=ChatEvents.MESSAGE_STARTED,
                data={"conversation_id": conversation_id},
            )

            # Load conversation history as LangChain messages
            messages = await self.conversation_service.get_langchain_messages(
                conversation_id=conversation_id,
            )

            # Get the default agent
            agent = get_default_agent()

            # Stream agent response
            full_content = ""
            async for event in agent.astream_events(
                {"messages": messages},
                version="v2",
            ):
                event_kind = event.get("event")

                # Handle token streaming from chat model
                if event_kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        token = chunk.content
                        full_content += token
                        await gateway.emit_to_user(
                            user_id=user_id,
                            event=ChatEvents.MESSAGE_TOKEN,
                            data={
                                "conversation_id": conversation_id,
                                "token": token,
                            },
                        )

                # Handle tool start
                elif event_kind == "on_tool_start":
                    tool_name = event.get("name", "")
                    run_id = event.get("run_id", "")
                    await gateway.emit_to_user(
                        user_id=user_id,
                        event=ChatEvents.MESSAGE_TOOL_START,
                        data={
                            "conversation_id": conversation_id,
                            "tool_name": tool_name,
                            "tool_call_id": run_id,
                        },
                    )

                # Handle tool end
                elif event_kind == "on_tool_end":
                    run_id = event.get("run_id", "")
                    output = event.get("data", {}).get("output", "")
                    # Convert output to string if it's not already
                    result = str(output) if output else ""
                    await gateway.emit_to_user(
                        user_id=user_id,
                        event=ChatEvents.MESSAGE_TOOL_END,
                        data={
                            "conversation_id": conversation_id,
                            "tool_call_id": run_id,
                            "result": result,
                        },
                    )

            # Save assistant message to database
            assistant_message = await self.conversation_service.add_message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=full_content,
                metadata=MessageMetadata(),
            )

            # Emit MESSAGE_COMPLETED event
            await gateway.emit_to_user(
                user_id=user_id,
                event=ChatEvents.MESSAGE_COMPLETED,
                data={
                    "conversation_id": conversation_id,
                    "message_id": assistant_message.id,
                    "content": full_content,
                    "metadata": None,
                },
            )

        except Exception as e:
            logger.exception(
                "Error processing agent response for conversation %s",
                conversation_id,
            )
            # Emit MESSAGE_FAILED event
            await gateway.emit_to_user(
                user_id=user_id,
                event=ChatEvents.MESSAGE_FAILED,
                data={
                    "conversation_id": conversation_id,
                    "error": str(e),
                },
            )
