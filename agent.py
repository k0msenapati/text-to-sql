from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from nodes import execute_sql, generate_sql, load_schema, format_answer
from state import AgentState

graph_builder = StateGraph(AgentState)

graph_builder.add_node(load_schema)
graph_builder.add_node(generate_sql)
graph_builder.add_node(execute_sql)
graph_builder.add_node(format_answer)

graph_builder.add_edge(START, "load_schema")
graph_builder.add_edge("load_schema", "generate_sql")
graph_builder.add_edge("generate_sql", "execute_sql")
graph_builder.add_edge("execute_sql", "format_answer")
graph_builder.add_edge("format_answer", END)

memory = InMemorySaver()

agent = graph_builder.compile(checkpointer=memory)
