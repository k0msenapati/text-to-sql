import logging

from database import get_schema, run_query, validate_sql_query
from sql import format_sql_answer, generate_sql_query, repair_sql_query
from state import AgentState

logger = logging.getLogger(__name__)


def load_schema(state: AgentState):
    try:
        schema = str(get_schema())
        logger.info("[load_schema] Schema loaded successfully")
        return {"schema": schema}
    except Exception as e:
        logger.error("[load_schema] Failed to load schema: %s", e)
        raise


def generate_sql(state: AgentState):
    question = state.get("question")
    if not question or not question.strip():
        raise ValueError("[generate_sql] 'question' is missing or empty in state")

    schema = state.get("schema")
    if schema is None:
        raise ValueError("[generate_sql] 'schema' is missing or None in state")

    try:
        sql = generate_sql_query(question=question, schema=schema)
        logger.info("[generate_sql] Generated SQL: %s", sql)
        return {"sql_query": sql, "retry_count": 0}
    except Exception as e:
        logger.error("[generate_sql] Failed to generate SQL: %s", e)
        raise


def validate_sql(state: AgentState):
    sql_query = state.get("sql_query")
    if not sql_query or not sql_query.strip():
        logger.warning("[validate_sql] 'sql_query' is missing or empty in state")
        return {
            "is_valid": False,
            "validation_error": "SQL query is missing or empty",
        }

    validation = validate_sql_query(sql_query)
    return {
        "is_valid": validation["is_valid"],
        "validation_error": validation["validation_error"],
    }


def repair_sql(state: AgentState):
    question = state.get("question")
    if not question or not question.strip():
        raise ValueError("[repair_sql] 'question' is missing or empty in state")

    schema = state.get("schema")
    if schema is None:
        raise ValueError("[repair_sql] 'schema' is missing or None in state")

    if state.get("sql_query") is None:
        raise ValueError("[repair_sql] 'sql_query' is missing or None in state")

    sql_query = state.get("sql_query", "")

    validation_error = state.get("validation_error") or "Unknown validation error"
    retry_count = (state.get("retry_count") or 0) + 1

    try:
        sql = repair_sql_query(
            question=question,
            schema=schema,
            sql_query=sql_query,
            validation_error=validation_error,
            retry_count=retry_count,
        )
        logger.info("[repair_sql] Retry %d/3 - Repaired SQL: %s", retry_count, sql)
        return {"sql_query": sql, "retry_count": retry_count}
    except Exception as e:
        logger.error("[repair_sql] Failed to repair SQL: %s", e)
        raise


def execute_sql(state: AgentState):
    sql_query = state.get("sql_query")
    if not sql_query or not sql_query.strip():
        raise ValueError("[execute_sql] 'sql_query' is missing or empty in state")

    try:
        sql_output = run_query(sql_query)
        logger.info("[execute_sql] SQL executed: %d row(s) returned", len(sql_output))
        return {"sql_output": str(sql_output)}
    except Exception as e:
        logger.error("[execute_sql] Failed to execute SQL '%s': %s", sql_query, e)
        raise


def format_answer(state: AgentState):
    if not state.get("is_valid", True):
        error_msg = state.get("validation_error") or "Failed to generate a valid SQL query."
        return {
            "answer": f"I was unable to retrieve the data because the SQL query could not be validated: {error_msg}"
        }

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
        return {"answer": answer}
    except Exception as e:
        logger.error("[format_answer] Failed to format answer: %s", e)
        raise
