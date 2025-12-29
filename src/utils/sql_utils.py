import re

def parse_llm_response(text: str):
    sections = {"sql": None, "explanation": None, "plot": None}

    if "SQL_QUERY:" in text:
        sections["sql"] = text.split("SQL_QUERY:")[1].split("EXPLANATION:")[0].strip()

    if "EXPLANATION:" in text:
        sections["explanation"] = text.split("EXPLANATION:")[1].split("PLOT_CODE:")[0].strip()

    return sections

def clean_sql(sql_text: str) -> str:
    """
    Remove markdown code fences and language hints from SQL
    """
    if not sql_text:
        return sql_text

    # Remove ```sql and ```
    sql_text = re.sub(r"```sql", "", sql_text, flags=re.IGNORECASE)
    sql_text = re.sub(r"```", "", sql_text)

    return sql_text.strip()
