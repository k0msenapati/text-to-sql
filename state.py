from typing import Annotated, TypedDict


class AgentState(TypedDict):
    question: str
    schema: str
    sql_query: str
    sql_output: str
    answer: str
