from langgraph.graph.state import CompiledStateGraph


def get_graph(agent: CompiledStateGraph) -> str:
    """Returns the ASCII representation of the compiled LangGraph agent."""
    graph = agent.get_graph()
    return graph.draw_ascii()


def get_mermaid_graph(agent: CompiledStateGraph, with_styles: bool = False) -> str:
    """Returns the Mermaid diagram string of the compiled LangGraph agent."""
    graph = agent.get_graph()
    return graph.draw_mermaid(with_styles=with_styles)
