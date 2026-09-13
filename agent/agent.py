from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    execute_sql,
    format_answer,
    generate_sql,
    load_schema,
    repair_sql,
    validate_sql,
)
from agent.state import AgentState

graph_builder = StateGraph(AgentState)

graph_builder.add_node(load_schema)
graph_builder.add_node(generate_sql)
graph_builder.add_node(validate_sql)
graph_builder.add_node(repair_sql)
graph_builder.add_node(execute_sql)
graph_builder.add_node(format_answer)

graph_builder.add_edge(START, "load_schema")
graph_builder.add_edge("load_schema", "generate_sql")
graph_builder.add_edge("generate_sql", "validate_sql")


def route_after_validation(state: AgentState) -> str:
    if state.get("is_valid"):
        return "execute_sql"
    if (state.get("retry_count") or 0) < 3:
        return "repair_sql"
    return "format_answer"

graph_builder.add_conditional_edges(
    "validate_sql",
    route_after_validation,
    {
        "execute_sql": "execute_sql",
        "repair_sql": "repair_sql",
        "format_answer": "format_answer",
    },
)

graph_builder.add_edge("repair_sql", "validate_sql")

graph_builder.add_edge("execute_sql", "format_answer")
graph_builder.add_edge("format_answer", END)

memory = InMemorySaver()

agent = graph_builder.compile(checkpointer=memory)
