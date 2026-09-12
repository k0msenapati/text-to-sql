import logging
from langchain.messages import HumanMessage, SystemMessage

from db import db_manager
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

        return {"sql_query": sql}

    except Exception as e:
        logger.error("[generate_sql] Failed to generate SQL: %s", e)
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
    system_prompt = prompts.FORMAT_ANSWER_SYSTEM_PROMPT
    user_prompt = prompts.FORMAT_ANSWER_HUMAN_PROMPT.format(
        question=state["question"],
        sql_query=state["sql_query"],
        sql_output=state["sql_output"],
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
