from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    clarification_engine,
    classify_intent,
    diagnose_execution_error,
    execute_sql,
    format_answer,
    format_meta,
    generate_sql,
    handle_out_of_scope_query,
    load_schema,
    repair_sql,
    validate_sql,
)
from agent.state import AgentState

graph_builder = StateGraph(AgentState)

# Nodes
graph_builder.add_node(classify_intent)
graph_builder.add_node(clarification_engine)
graph_builder.add_node(load_schema)
graph_builder.add_node(generate_sql)
graph_builder.add_node(validate_sql)
graph_builder.add_node(repair_sql)
graph_builder.add_node(execute_sql)
graph_builder.add_node(diagnose_execution_error)
graph_builder.add_node(format_answer)
graph_builder.add_node(format_meta)
graph_builder.add_node(handle_out_of_scope_query)

# Intent classification routing
graph_builder.add_edge(START, "classify_intent")


def route_after_intent(state: AgentState) -> str:
    intent = state.get("intent")
    if intent == "metadata_query":
        return "format_meta"
    if intent == "ambiguous_query":
        return "clarification_engine"
    if intent == "out_of_scope_query":
        return "handle_out_of_scope_query"
    return "load_schema"


graph_builder.add_conditional_edges(
    "classify_intent",
    route_after_intent,
    {
        "load_schema": "load_schema",
        "format_meta": "format_meta",
        "clarification_engine": "clarification_engine",
        "handle_out_of_scope_query": "handle_out_of_scope_query",
    },
)


def route_after_clarification(state: AgentState) -> str:
    if state.get("clarification_needed"):
        return END
    return "load_schema"


graph_builder.add_conditional_edges(
    "clarification_engine",
    route_after_clarification,
    {
        "load_schema": "load_schema",
        END: END,
    },
)

# Data query flow (existing agent flow)
graph_builder.add_edge("load_schema", "generate_sql")
graph_builder.add_edge("generate_sql", "validate_sql")


def route_after_validation(state: AgentState) -> str:
    if state.get("is_valid"):
        return "execute_sql"
    if (state.get("validation_retry_count") or 0) < 3:
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


def route_after_execution(state: AgentState) -> str:
    if not state.get("execution_error"):
        return "format_answer"
    if (state.get("execution_retry_count") or 0) < 3:
        return "diagnose_execution_error"
    return "format_answer"


graph_builder.add_conditional_edges(
    "execute_sql",
    route_after_execution,
    {
        "format_answer": "format_answer",
        "diagnose_execution_error": "diagnose_execution_error",
    },
)

graph_builder.add_edge("diagnose_execution_error", "repair_sql")
graph_builder.add_edge("format_answer", END)

# Terminal edges for non-data query flows
graph_builder.add_edge("format_meta", END)
graph_builder.add_edge("handle_out_of_scope_query", END)

memory = InMemorySaver()

agent = graph_builder.compile(checkpointer=memory)
