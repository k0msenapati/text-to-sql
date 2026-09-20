from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]

    question: str
    intent: str | None
    schema: str | None
    sql_query: str | None

    is_valid: bool | None
    validation_error: str | None
    validation_retry_count: int | None

    execution_error: str | None
    execution_retry_count: int | None
    diagnosis: str | None

    sql_output: str | None
    answer: str | None
    clarification_needed: bool | None
