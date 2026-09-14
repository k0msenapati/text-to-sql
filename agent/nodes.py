import logging

from classifier import classify_query_intent
from database import get_schema, run_query, validate_sql_query
from metadata import format_meta_answer
from sql import (
    diagnose_execution_error as diagnose_execution_error_query,
    format_sql_answer,
    generate_sql_query,
    repair_sql_query,
)
from agent.state import AgentState

logger = logging.getLogger(__name__)

AMBIGUOUS_QUERY_RESPONSE = (
    "Your query is ambiguous and requires additional information. "
    "I cannot reply without more context. Please clarify your request."
)

OUT_OF_SCOPE_FALLBACK_MESSAGE = (
    "I am a Text-to-SQL assistant designed to answer questions about the database. "
    "Your request is out of scope. Please ask a database-related question."
)


def classify_intent(state: AgentState):
    question = state.get("question")
    if not question or not question.strip():
        raise ValueError("[classify_intent] 'question' is missing or empty in state")

    try:
        intent = classify_query_intent(question=question)
        logger.info("[classify_intent] Classified intent: %s", intent)
        return {"intent": intent}
    except Exception as e:
        logger.error("[classify_intent] Failed to classify intent: %s", e)
        raise


def format_meta(state: AgentState):
    question = state.get("question")
    if not question or not question.strip():
        raise ValueError("[format_meta] 'question' is missing or empty in state")

    schema = state.get("schema")
    if not schema:
        schema = str(get_schema())

    try:
        answer = format_meta_answer(question=question, schema=schema)
        logger.info("[format_meta] Metadata answer formatted")
        return {"schema": schema, "answer": answer}
    except Exception as e:
        logger.error("[format_meta] Failed to format metadata answer: %s", e)
        raise


def handle_ambiguous_query(state: AgentState):
    logger.info("[handle_ambiguous_query] Handling ambiguous query")
    return {"answer": AMBIGUOUS_QUERY_RESPONSE}


def handle_out_of_scope_query(state: AgentState):
    logger.info("[handle_out_of_scope_query] Handling out-of-scope query")
    return {"answer": OUT_OF_SCOPE_FALLBACK_MESSAGE}


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
        return {
            "sql_query": sql,
            "validation_retry_count": 0,
            "execution_retry_count": 0,
            "execution_error": None,
            "diagnosis": None,
        }
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


def diagnose_execution_error(state: AgentState):
    sql_query = state.get("sql_query")
    execution_error = state.get("execution_error") or "Unknown database execution error"
    schema = state.get("schema")

    if not sql_query or not sql_query.strip():
        raise ValueError(
            "[diagnose_execution_error] 'sql_query' is missing or empty in state"
        )
    if schema is None:
        raise ValueError(
            "[diagnose_execution_error] 'schema' is missing or None in state"
        )

    execution_retry_count = (state.get("execution_retry_count") or 0) + 1

    try:
        diagnosis = diagnose_execution_error_query(
            sql_query=sql_query,
            execution_error=execution_error,
            schema=schema,
        )
        logger.info(
            "[diagnose_execution_error] Retry %d/3 - Diagnosis: %s",
            execution_retry_count,
            diagnosis,
        )
        return {
            "diagnosis": diagnosis,
            "execution_retry_count": execution_retry_count,
        }
    except Exception as e:
        logger.error(
            "[diagnose_execution_error] Failed to diagnose execution error: %s", e
        )
        raise


def repair_sql(state: AgentState):
    question = state.get("question") or ""
    schema = state.get("schema")
    sql_query = state.get("sql_query")

    if schema is None:
        raise ValueError("[repair_sql] 'schema' is missing or None in state")
    if sql_query is None:
        raise ValueError("[repair_sql] 'sql_query' is missing or None in state")

    validation_error = state.get("validation_error")
    execution_error = state.get("execution_error")
    diagnosis = state.get("diagnosis")

    if validation_error:
        validation_retry_count = (state.get("validation_retry_count") or 0) + 1
    else:
        validation_retry_count = state.get("validation_retry_count") or 0

    try:
        sql = repair_sql_query(
            sql_query=sql_query,
            schema=schema,
            question=question,
            validation_error=validation_error,
            execution_error=execution_error,
            diagnosis=diagnosis,
        )
        logger.info("[repair_sql] Repaired SQL: %s", sql)
        return {
            "sql_query": sql,
            "validation_retry_count": validation_retry_count,
            "validation_error": None,
            "execution_error": None,
            "diagnosis": None,
        }
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
        return {
            "sql_output": str(sql_output),
            "execution_error": None,
        }
    except Exception as e:
        logger.warning(
            "[execute_sql] Database execution failed for query '%s': %s", sql_query, e
        )
        return {
            "sql_output": None,
            "execution_error": str(e),
        }


def format_answer(state: AgentState):
    if state.get("execution_error"):
        error_msg = state.get("execution_error")
        diagnosis = state.get("diagnosis")
        diag_suffix = f" Diagnosis: {diagnosis}" if diagnosis else ""
        return {
            "answer": f"I was unable to retrieve the data because a database execution error occurred: {error_msg}.{diag_suffix}"
        }

    if not state.get("is_valid", True):
        error_msg = (
            state.get("validation_error") or "Failed to generate a valid SQL query."
        )
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
