from langchain_core.prompts import ChatPromptTemplate

template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert data analyst generating SQL for DuckDB.

STRICT RULES:
- There is ONLY ONE TABLE available
- Table name is EXACT and CASE-SENSITIVE
- You MUST use the table name exactly as provided
- Do NOT invent or rename tables
- Do NOT pluralize table names
- Generate ONLY executable SQL

Explain results in simple language.
"""
        ),
        (
            "user",
            """
Available database information:

Table name (EXACT, case-sensitive):
{table_name}

Table schema:
{schema}

User question:
{user_query}

IMPORTANT:
- Use ONLY the table name: {table_name}
- Do NOT use any other table names

Respond in this format:

SQL_QUERY:
<sql>

EXPLANATION:
<text>
"""
        ),
    ]
)
