def clean_sql_query(raw_sql: str) -> str:
    """
    Cleans raw SQL response from an LLM by stripping markdown code fences
    (e.g., ```sql ... ``` or ``` ... ```) and leading/trailing whitespace.
    """
    if not raw_sql:
        return ""

    sql = raw_sql.strip()

    if sql.startswith("```"):
        lines = sql.splitlines()
        # Remove opening code fence (e.g. ```sql or ```)
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        # Remove closing code fence (```)
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        sql = "\n".join(lines).strip()

    return sql
