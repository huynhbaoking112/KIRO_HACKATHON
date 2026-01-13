"""Response formatter node for formatting final responses."""

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.graphs.workflows.chat_workflow.state import ChatWorkflowState
from app.infrastructure.llm.factory import get_chat_openai
from app.prompts.system.response_formatter import RESPONSE_FORMATTER_PROMPT

logger = logging.getLogger(__name__)


async def response_formatter_node(state: ChatWorkflowState) -> dict:
    """Format the final response for the user.

    Takes the agent_response from the previous node and formats it
    with Vietnamese locale (numbers with dots, currency with VND suffix).

    Args:
        state: Current workflow state containing agent_response

    Returns:
        dict with "final_response" key containing the formatted response
    """
    agent_response = state.get("agent_response")

    # If no agent response, return error message
    if not agent_response:
        logger.warning("No agent response to format")
        return {
            "final_response": "Xin lỗi, tôi không thể xử lý yêu cầu của bạn. "
            "Vui lòng thử lại."
        }

    try:
        llm = get_chat_openai(temperature=0.3, streaming=True)

        # Get the original user question for context
        messages = state.get("messages", [])
        user_question = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage) or (
                hasattr(msg, "type") and msg.type == "human"
            ):
                user_question = msg.content if hasattr(msg, "content") else str(msg)
                break

        # Create formatting prompt
        format_prompt = f"""Câu hỏi của người dùng: {user_question}

Kết quả cần format:
{agent_response}

Hãy format kết quả trên theo quy tắc đã cho."""

        response = await llm.ainvoke(
            [
                SystemMessage(content=RESPONSE_FORMATTER_PROMPT),
                HumanMessage(content=format_prompt),
            ]
        )

        final_response = response.content

        logger.info("Response formatted: %s...", final_response[:50])
        return {"final_response": final_response}

    except Exception:
        logger.exception("Response formatting failed")
        # Return the original response if formatting fails
        return {"final_response": agent_response}
