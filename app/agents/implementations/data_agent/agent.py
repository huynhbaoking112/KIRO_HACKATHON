"""Data Agent implementation using LangGraph ReAct pattern.

This agent queries user's business data using custom tools.
Implementation will be completed in Task 5.
"""

from typing import Any

from langgraph.graph.state import CompiledStateGraph


def create_data_agent(user_connections: list[dict[str, Any]]) -> CompiledStateGraph:
    """Create a ReAct agent with data query tools.

    Args:
        user_connections: List of user's sheet connections with schemas

    Returns:
        A compiled LangGraph agent ready for streaming execution.

    Note:
        Full implementation in Task 5.
    """
    # Placeholder - will be implemented in Task 5
    raise NotImplementedError("Data agent implementation pending - see Task 5")
