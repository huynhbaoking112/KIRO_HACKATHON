"""Data Agent implementation using LangGraph ReAct pattern.

This agent handles data queries using custom tools bound to user's connections.
It uses the ReAct pattern for reasoning and tool execution.

Requirements: 4.1, 5.1, 6.1, 7.1, 8.1
"""

from typing import Any

from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

from app.agents.implementations.data_agent.tools import (
    create_aggregate_data_tool,
    create_compare_periods_tool,
    create_execute_aggregation_tool,
    create_get_data_schema_tool,
    create_get_top_items_tool,
)
from app.infrastructure.llm.factory import get_chat_openai
from app.prompts.system.data_agent import DATA_AGENT_SYSTEM_PROMPT


def format_schema_context(user_connections: list[dict[str, Any]]) -> str:
    """Format user connections into schema context for the system prompt.

    Args:
        user_connections: List of user's sheet connections with schemas.
            Each connection should have:
            - connection_name: Name of the connection
            - connection_id: Unique identifier
            - fields: List of field definitions with name, type, sample_values

    Returns:
        Formatted string describing available data sources and their schemas.
    """
    if not user_connections:
        return "No data sources available. User needs to set up data sync first."

    lines = []
    for conn in user_connections:
        conn_name = conn.get("connection_name", "Unknown")
        fields = conn.get("fields", [])

        lines.append(f"### {conn_name}")

        if fields:
            lines.append("Fields:")
            for field in fields:
                field_name = field.get("name", "unknown")
                field_type = field.get("type", "string")
                sample_values = field.get("sample_values", [])

                # Format sample values (show max 3)
                samples_str = ""
                if sample_values:
                    samples = sample_values[:3]
                    samples_str = f" (e.g., {', '.join(str(s) for s in samples)})"

                lines.append(f"  - {field_name} ({field_type}){samples_str}")
        else:
            lines.append("  (No field information available)")

        lines.append("")  # Empty line between connections

    return "\n".join(lines)


def create_data_agent(user_connections: list[dict[str, Any]]) -> CompiledStateGraph:
    """Create a ReAct agent with data query tools bound to user's connections.

    This agent is created per-request with the user's specific connections,
    ensuring data isolation between users.

    Args:
        user_connections: List of user's sheet connections with schemas.
            Each connection should contain:
            - connection_id: Unique identifier for the connection
            - connection_name: Human-readable name
            - fields: List of field definitions
            - sync_enabled: Whether sync is active

    Returns:
        A compiled LangGraph agent ready for streaming execution.

    Requirements:
        - 4.1: get_data_schema tool for schema discovery
        - 5.1: aggregate_data tool for simple aggregations
        - 6.1: get_top_items tool for top N queries
        - 7.1: compare_periods tool for period comparison
        - 8.1: execute_aggregation tool for custom pipelines
    """
    # Create LLM instance
    llm = get_chat_openai(
        temperature=0.3,  # Lower temperature for more consistent data queries
        streaming=True,
    )

    # Create tools bound to user's connections
    tools = [
        create_get_data_schema_tool(user_connections),
        create_aggregate_data_tool(user_connections),
        create_get_top_items_tool(user_connections),
        create_compare_periods_tool(user_connections),
        create_execute_aggregation_tool(user_connections),
    ]

    # Format schema context for the system prompt
    schema_context = format_schema_context(user_connections)
    system_prompt = DATA_AGENT_SYSTEM_PROMPT.format(schema_context=schema_context)

    # Create ReAct agent with tools and prompt
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
    )

    return agent
