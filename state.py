from typing import TypedDict


class AgentState(TypedDict, total=False):
    question: str
    schema: str | None
    sql_query: str | None

    is_valid: bool | None
    validation_error: str | None
    retry_count: int | None

    sql_output: str | None
    answer: str | None
