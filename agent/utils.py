from langgraph.graph.state import CompiledStateGraph


def get_graph(agent: CompiledStateGraph) -> str:
    graph = agent.get_graph()
    return graph.draw_ascii()


def get_mermaid_graph(agent: CompiledStateGraph) -> str:
    graph = agent.get_graph()
    return graph.draw_mermaid()
