"""Agent registry/factory for managing agent instances."""

from functools import lru_cache

from langgraph.graph.state import CompiledStateGraph

from app.agents.implementations.default_agent.agent import create_default_agent


@lru_cache
def get_default_agent() -> CompiledStateGraph:
    """Get singleton default agent instance.

    Returns:
        Cached CompiledStateGraph instance of the default ReAct agent.
    """
    return create_default_agent()
