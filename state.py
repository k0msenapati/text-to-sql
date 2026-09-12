from typing import TypedDict


class AgentState(TypedDict):
    question: str
    schema: str
    sql_query: str

    is_valid: bool
    validation_error: str
    retry_count: int

    sql_output: str
    answer: str
