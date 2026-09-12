import logging
from langchain.messages import HumanMessage, SystemMessage

from db import db_manager
from model import llm
from state import AgentState

logger = logging.getLogger(__name__)


def load_schema(state: AgentState):
    try:
        schema = str(db_manager.get_schema())
        logger.info("[load_schema] Schema loaded successfully")

        return {"schema": schema}

    except Exception as e:
        logger.error("Failed to load schema: %s", e)
        raise


def generate_sql(state: AgentState):
    database_schema = state["schema"]
    database_dialect = "sqlite"
    user_query = state["question"]

    system_prompt = f"""You are an expert AI assistant that converts natural language questions into highly accurate SQL queries. 

Given the following SQL database schema, understand the tables, columns, and relationships:

<schema>
{database_schema}
</schema>

### Instructions:
1. Review the database schema carefully. Do not guess or invent column/table names.
2. Generate a single valid SQL query matching the user's request.
3. Ensure the syntax is compatible with {database_dialect} (e.g., PostgreSQL, MySQL, SQLite).
4. Provide ONLY the raw SQL query. Do not include markdown code block formatting (```sql), explanation text, or conversational filler."""

    user_prompt = f"""Convert the following natural language query into SQL:
<query>
{user_query}
</query>"""

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
        logger.error("Failed to generate SQL: %s", e)
        raise


def execute_sql(state: AgentState):
    sql_query = state["sql_query"]

    try:
        sql_output = db_manager.run_query(sql_query)
        logger.info("[execute_sql] SQL executed: %d row(s) returned", len(sql_output))

        return {"sql_output": str(sql_output)}

    except Exception as e:
        logger.error("Failed to execute SQL '%s': %s", sql_query, e)
        raise
