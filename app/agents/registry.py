"""Agent registry/factory for managing agent instances."""

from functools import lru_cache
from typing import Any

from langgraph.graph.state import CompiledStateGraph

from app.agents.implementations.data_agent.agent import create_data_agent
from app.agents.implementations.default_agent.agent import create_default_agent


@lru_cache
def get_default_agent() -> CompiledStateGraph:
    """Get singleton default agent instance.

    Returns:
        Cached CompiledStateGraph instance of the default ReAct agent.
    """
    return create_default_agent()


def get_data_agent(user_connections: list[dict[str, Any]]) -> CompiledStateGraph:
    """Create a data agent instance bound to user's connections.

    Note: This is NOT cached because each user has different connections.
    A new agent is created per request with the user's specific data context.

    Args:
        user_connections: List of user's sheet connections with schemas.
            Each connection should contain connection_id, connection_name,
            fields, and sync_enabled.

    Returns:
        CompiledStateGraph instance of the data agent with user's tools.

    Requirements: 14.1
    """
    return create_data_agent(user_connections)
