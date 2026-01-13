"""Clarify node for asking users to clarify unclear messages."""

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.graphs.workflows.chat_workflow.state import ChatWorkflowState
from app.infrastructure.llm.factory import get_chat_openai
from app.prompts.system.clarify_node import CLARIFY_NODE_PROMPT

logger = logging.getLogger(__name__)


async def clarify_node(state: ChatWorkflowState) -> dict:
    """Ask user to clarify their unclear message.

    Provides examples of supported queries to help the user
    formulate a clearer question.

    Args:
        state: Current workflow state containing messages and context

    Returns:
        dict with "agent_response" key containing the clarification request
    """
    try:
        llm = get_chat_openai(temperature=0.7, streaming=True)

        # Build messages for LLM
        llm_messages = [SystemMessage(content=CLARIFY_NODE_PROMPT)]

        # Add recent conversation for context
        messages = state.get("messages", [])
        for msg in messages[-5:]:  # Last 5 messages
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

        logger.info("Clarify node generated response: %s...", agent_response[:50])
        return {"agent_response": agent_response}

    except Exception:
        logger.exception("Clarify node failed")
        # Fallback response in both languages
        return {
            "agent_response": "I'm not sure I understand your question. "
            "You can ask me about:\n"
            "- Total revenue, order counts\n"
            "- Top-selling products\n"
            "- Revenue comparisons between periods\n"
            "- Analysis by platform (Shopee, Lazada...)\n\n"
            "Tôi chưa hiểu rõ câu hỏi của bạn. Bạn có thể hỏi về:\n"
            "- Tổng doanh thu, số đơn hàng\n"
            "- Top sản phẩm bán chạy\n"
            "- So sánh doanh thu giữa các kỳ\n"
            "- Phân tích theo platform (Shopee, Lazada...)"
        }
