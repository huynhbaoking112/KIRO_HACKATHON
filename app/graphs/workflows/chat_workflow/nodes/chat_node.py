"""Chat node for handling general conversation."""

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.graphs.workflows.chat_workflow.state import ChatWorkflowState
from app.infrastructure.llm.factory import get_chat_openai
from app.prompts.system.chat_node import CHAT_NODE_PROMPT

logger = logging.getLogger(__name__)


async def chat_node(state: ChatWorkflowState) -> dict:
    """Handle general conversation with the user.

    Responds to greetings, questions about capabilities, and general chitchat
    in a friendly manner using Vietnamese language.

    Args:
        state: Current workflow state containing messages and context

    Returns:
        dict with "agent_response" key containing the response string
    """
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

        response = await llm.ainvoke(llm_messages)
        agent_response = response.content

        logger.info("Chat node generated response: %s...", agent_response[:50])
        return {"agent_response": agent_response}

    except Exception:
        logger.exception("Chat node failed")
        return {
            "agent_response": "Sorry, I'm having trouble processing your message. Please try again later."
        }
