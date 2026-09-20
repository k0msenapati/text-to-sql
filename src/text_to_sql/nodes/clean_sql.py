import re


def clean_sql_query(raw_sql: str) -> str:
    """
    Cleans raw SQL response from an LLM by stripping markdown code fences
    (e.g., ```sql ... ``` or ``` ... ```), extracting the code block if surrounded
    by conversational text, and stripping leading/trailing whitespace.
    """
    if not raw_sql or not raw_sql.strip():
        return ""

    text = raw_sql.strip()

    # Extract content inside markdown code fence if present
    match = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        sql = match.group(1).strip()
    else:
        # Handle opening code fence without closing fence
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            sql = "\n".join(lines).strip()
        else:
            sql = text

    # Strip conversational preface if not starting with SELECT, WITH, or SQL comment
    if not (
        sql.lower().startswith("select")
        or sql.lower().startswith("with")
        or sql.startswith("--")
        or sql.startswith("/*")
    ):
        keyword_match = re.search(r"\b(SELECT|WITH)\b", sql, re.IGNORECASE)
        if keyword_match:
            sql = sql[keyword_match.start() :].strip()

    return sql
