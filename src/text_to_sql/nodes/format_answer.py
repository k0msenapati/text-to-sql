import logging
from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from text_to_sql.llm import llm as default_llm
from text_to_sql.prompts import FORMAT_ANSWER_HUMAN_PROMPT, FORMAT_ANSWER_SYSTEM_PROMPT
from text_to_sql.state import AgentState

logger = logging.getLogger(__name__)


def format_sql_answer(
    question: str,
    sql_query: str,
    sql_output: str,
    model: BaseChatModel | None = None,
) -> str:
    """
    Transforms raw SQL execution results into a clean, natural language response using the LLM.
    """
    client = model if model is not None else default_llm

    system_prompt = FORMAT_ANSWER_SYSTEM_PROMPT
    user_prompt = FORMAT_ANSWER_HUMAN_PROMPT.format(
        question=question,
        sql_query=sql_query,
        sql_output=sql_output,
    )

    response = client.invoke(
        [
            SystemMessage(system_prompt),
            HumanMessage(user_prompt),
        ]
    )

    return str(response.content)


def format_answer(state: AgentState):
    """LangGraph node: Formats data query results or runtime failure messages into plain English."""
    if state.get("execution_error"):
        error_msg = state.get("execution_error")
        diagnosis = state.get("diagnosis")
        diag_suffix = f" Diagnosis: {diagnosis}" if diagnosis else ""
        answer = f"I was unable to retrieve the data because a database execution error occurred: {error_msg}.{diag_suffix}"
        return {"answer": answer, "messages": [AIMessage(content=answer)]}

    if not state.get("is_valid", True):
        error_msg = (
            state.get("validation_error") or "Failed to generate a valid SQL query."
        )
        answer = f"I was unable to retrieve the data because the SQL query could not be validated: {error_msg}"
        return {"answer": answer, "messages": [AIMessage(content=answer)]}

    question = state.get("question")
    if not question or not question.strip():
        raise ValueError("[format_answer] 'question' is missing or empty in state")

    sql_query = state.get("sql_query") or ""
    sql_output = state.get("sql_output") or ""

    try:
        answer = format_sql_answer(
            question=question,
            sql_query=sql_query,
            sql_output=sql_output,
        )
        logger.info("[format_answer] Answer formatted")
        return {"answer": answer, "messages": [AIMessage(content=answer)]}
    except Exception as e:
        logger.error("[format_answer] Failed to format answer: %s", e)
        raise
