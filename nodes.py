import logging
from langchain.messages import HumanMessage, SystemMessage

from database import db_manager, validate_sql_query
from model import llm
from state import AgentState
import prompts

logger = logging.getLogger(__name__)


def load_schema(state: AgentState):
    try:
        schema = str(db_manager.get_schema())
        logger.info("[load_schema] Schema loaded successfully")

        return {"schema": schema}

    except Exception as e:
        logger.error("[load_schema] Failed to load schema: %s", e)
        raise


def generate_sql(state: AgentState):
    system_prompt = prompts.GENERATE_SQL_SYSTEM_PROMPT.format(database_dialect="sqlite")
    user_prompt = prompts.GENERATE_SQL_HUMAN_PROMPT.format(
        schema=state["schema"], question=state["question"]
    )

    try:
        response = llm.invoke(
            [
                SystemMessage(system_prompt),
                HumanMessage(user_prompt),
            ]
        )
        sql = str(response.content).strip()

        if sql.startswith("```"):
            lines = sql.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            sql = "\n".join(lines).strip()

        logger.info("[generate_sql] Generated SQL: %s", sql)

        return {"sql_query": sql, "retry_count": 0}

    except Exception as e:
        logger.error("[generate_sql] Failed to generate SQL: %s", e)
        raise


def validate_sql(state: AgentState):
    validation = validate_sql_query(state["sql_query"])
    return {
        "is_valid": validation["is_valid"],
        "validation_error": validation["validation_error"],
    }


def repair_sql(state: AgentState):
    retry_count = state.get("retry_count", 0) + 1
    system_prompt = prompts.REPAIR_SQL_SYSTEM_PROMPT
    user_prompt = prompts.REPAIR_SQL_HUMAN_PROMPT.format(
        schema=state["schema"],
        question=state["question"],
        sql_query=state["sql_query"],
        validation_error=state.get("validation_error", "Unknown validation error"),
    )

    try:
        response = llm.invoke(
            [
                SystemMessage(system_prompt),
                HumanMessage(user_prompt),
            ]
        )
        sql = str(response.content).strip()

        if sql.startswith("```"):
            lines = sql.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            sql = "\n".join(lines).strip()

        logger.info("[repair_sql] Retry %d/3 - Repaired SQL: %s", retry_count, sql)

        return {"sql_query": sql, "retry_count": retry_count}

    except Exception as e:
        logger.error("[repair_sql] Failed to repair SQL: %s", e)
        raise


def execute_sql(state: AgentState):
    sql_query = state["sql_query"]

    try:
        sql_output = db_manager.run_query(sql_query)
        logger.info("[execute_sql] SQL executed: %d row(s) returned", len(sql_output))

        return {"sql_output": str(sql_output)}

    except Exception as e:
        logger.error("[execute_sql] Failed to execute SQL '%s': %s", sql_query, e)
        raise


def format_answer(state: AgentState):
    if not state.get("is_valid", True):
        error_msg = state.get("validation_error", "Failed to generate a valid SQL query.")
        return {
            "answer": f"I was unable to retrieve the data because the SQL query could not be validated: {error_msg}"
        }

    system_prompt = prompts.FORMAT_ANSWER_SYSTEM_PROMPT
    user_prompt = prompts.FORMAT_ANSWER_HUMAN_PROMPT.format(
        question=state["question"],
        sql_query=state["sql_query"],
        sql_output=state.get("sql_output", ""),
    )

    try:
        response = llm.invoke(
            [
                SystemMessage(system_prompt),
                HumanMessage(user_prompt),
            ]
        )
        answer = response.content

        logger.info("[format_answer] Answer formatted")

        return {"answer": answer}

    except Exception as e:
        logger.error("[format_answer] Failed to format answer: %s", e)
        raise
