"""Chat node for handling general conversation.

Emits Socket.IO events directly for real-time token streaming.
"""

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.common.event_socket import ChatEvents
from app.graphs.workflows.chat_workflow.state import ChatWorkflowState
from app.infrastructure.llm.factory import get_chat_openai
from app.prompts.system.chat_node import CHAT_NODE_PROMPT
from app.socket_gateway import gateway

logger = logging.getLogger(__name__)


async def chat_node(state: ChatWorkflowState) -> dict:
    """Handle general conversation with the user.

    Responds to greetings, questions about capabilities, and general chitchat
    in a friendly manner using Vietnamese language. Streams tokens via Socket.IO.

    Args:
        state: Current workflow state containing messages and context

    Returns:
        dict with "agent_response" key containing the response string
    """
    user_id = state.get("user_id", "")
    conversation_id = state.get("conversation_id", "")

    try:
        llm = get_chat_openai(temperature=0.7, streaming=True)

        # Build messages for LLM
        llm_messages = [SystemMessage(content=CHAT_NODE_PROMPT)]

        # Add conversation history
        messages = state.get("messages", [])
        for msg in messages[-10:]:  # Last 10 messages for context
            if hasattr(msg, "content"):
                if isinstance(msg, HumanMessage) or (
                    hasattr(msg, "type") and msg.type == "human"
                ):
                    llm_messages.append(HumanMessage(content=msg.content))
                elif isinstance(msg, AIMessage) or (
                    hasattr(msg, "type") and msg.type == "ai"
                ):
                    llm_messages.append(AIMessage(content=msg.content))

        # Stream response with Socket.IO emit
        full_content = ""
        async for chunk in llm.astream(llm_messages):
            if chunk.content:
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

        logger.info("Chat node generated response: %s...", full_content[:50])
        return {"agent_response": full_content}

    except Exception:
        logger.exception("Chat node failed")
        return {
            "agent_response": "Sorry, I'm having trouble processing your message. Please try again later."
        }
