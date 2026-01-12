"""Graph registry for managing LangGraph workflows.

Provides factory functions to create and retrieve graph instances.
"""

from typing import Callable, Dict, Any
from langgraph.graph.state import CompiledStateGraph

# Registry of graph factories
_graph_registry: Dict[str, Callable[..., CompiledStateGraph]] = {}


def register_graph(name: str, factory: Callable[..., CompiledStateGraph]) -> None:
    """Register a graph factory function.

    Args:
        name: Unique identifier for the graph
        factory: Factory function that creates the compiled graph
    """
    _graph_registry[name] = factory


def get_graph(name: str, **kwargs: Any) -> CompiledStateGraph:
    """Get a compiled graph by name.

    Args:
        name: The registered graph name
        **kwargs: Arguments to pass to the graph factory

    Returns:
        Compiled LangGraph StateGraph

    Raises:
        KeyError: If graph name is not registered
    """
    if name not in _graph_registry:
        raise KeyError(
            f"Graph '{name}' not found. Available: {list(_graph_registry.keys())}"
        )
    return _graph_registry[name](**kwargs)


def list_graphs() -> list[str]:
    """List all registered graph names."""
    return list(_graph_registry.keys())
