from pathlib import Path
import sys
import duckdb
import pandas as pd
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from config import get_config
import os

cfg=get_config()
os.environ["TAVILY_API_KEY"] = cfg["keys"]["tavily_api_key"]

from langchain.tools import tool
from langchain_tavily import TavilySearch
from mistralai import Mistral
import base64
from src.utils.pdf_processor import TextProcessor
from src.utils.log import AppLogger
from langchain_mistralai import ChatMistralAI
from src.prompts.sql_system_prompt import template
from src.utils import sql_utils
logger = AppLogger.setup()

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


class Tools:
    def __init__(self):
        self.mistral_api_key = cfg["keys"]["mistral_api_key"]
        self.client = Mistral(api_key=self.mistral_api_key)
        self.vision_model = "mistral-small-latest"
        self.audio_model="voxtral-mini-latest"
        self.llm = ChatMistralAI(
                model="codestral-latest",
                temperature=0,
                api_key=self.mistral_api_key
            )
        self.multi_modal_agent = self.client.beta.agents.create(
            model="mistral-medium-2505",
            name="Multi-Modal Agent",
            description=(
                "Agent capable of complex reasoning using web search, "
                "code execution, and image generation."
            ),
            instructions=(
                "You are a Multi-Modal Agent.\n"
                "- Use `web_search` for real-time information\n"
                "- Use `code_interpreter` for calculations or code execution\n"
                "- Use `image_generation` to generate images\n"
                "- Combine tools when needed\n"
                "- Respond concisely and accurately"
            ),
            tools=[
                {"type": "web_search"},
                {"type": "code_interpreter"},
                {"type": "image_generation"},
            ],
            completion_args={
                "temperature": 0.3,
                "top_p": 0.95,
            }
        )

        self.multi_modal_conv_id = None


    def __call__(self):

        @tool
        def multimodal_tool(query: str):
            """
            Use the Multi-Modal Agent for complex reasoning tasks that may
            require web search, computation, or image generation.
            """
            try:
                logger.info("Calling Multi-Modal Agent")

                if not self.multi_modal_conv_id:
                    response = self.client.beta.conversations.start(
                        agent_id=self.multi_modal_agent.id,
                        inputs=query
                    )
                    self.multi_modal_conv_id = response.conversation_id
                else:
                    response = self.client.beta.conversations.append(
                        conversation_id=self.multi_modal_conv_id,
                        inputs=query
                    )

                # final_text = extract_final_text(response)
                logger.success("Multi-Modal Agent responded")
                return [{"content": response.outputs}]

            except Exception as e:
                logger.error(f"Multi-Modal Agent failed: {e}")
                return [{"content": "Multi-modal processing failed"}]



        @tool
        def query_from_pdf(file_path: str, file_name: str):
            """
            Extract and retrieve text content from a PDF file.

            Use this tool when the user asks questions that should be answered
            using the contents of an uploaded or local PDF document.

            Args:
                query (str): The user question related to the PDF.
                file_path (str): Directory path where the PDF is stored.
                file_name (str): Name of the PDF file.

            Returns:
                List[str]: Extracted text chunks from the PDF.
            """
            try:
                logger.info("calling query_from_pdf tool")
                
                text_processor = TextProcessor()
                docs = text_processor.extract_text(
                    file_path=str(file_path),
                    file_name=file_name
                )
                
                logger.success("query_from_pdf tool responded")
            except Exception as e:
                logger.error(f"query_from_pdf error due to : {e} ")
                docs=[{"content":"technical error"}]

            return docs

        @tool
        def query_from_image(query: str, image_path: str):
            """
            Analyze an image and answer a query using a vision-capable LLM.

            Use this tool when the input contains an image and the question
            requires visual understanding (e.g., text in image, objects, diagrams).

            Args:
                query (str): Question or instruction related to the image.
                image_path (str): Path to the image file.

            Returns:
                List[Dict]: Model-generated response based on image understanding.
            """
            try:
                logger.info("calling query_from_image tool")
                
                base64_image = encode_image(image_path)

                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": query},
                            {
                                "type": "image_url",
                                "image_url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        ]
                    }
                ]

                chat_response = self.client.chat.complete(
                    model=self.vision_model,
                    messages=messages
                )

                content = chat_response.choices[0].message.content
                logger.success("query_from_image tool responded")
              
                return [{"image_content": content}]
            except Exception as e:
                logger.error(f"query_from_image error due to : {e} ")
                return [{"content":"technical error in mistral"}]
        
        @tool
        def query_from_audio(query: str, audio_path: str):
            """
            Analyze an audio file and answer the user's query using an audio-capable LLM.

            Use this tool when:
            - The user provides an audio file
            - The task involves speech understanding, transcription, or audio-based reasoning

            Args:
                query (str): The user question or instruction related to the audio.
                audio_path (str): Path to the audio file on disk.

            Returns:
                List[Dict]: Model-generated response based on audio understanding.
            """
            try:
                logger.info("calling query_from_audio tool")
                
                # Encode audio file as base64
                with open(audio_path, "rb") as f:
                    content = f.read()

                audio_base64 = base64.b64encode(content).decode("utf-8")

                chat_response = self.client.chat.complete(
                    model=self.audio_model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "input_audio",
                                    "input_audio": audio_base64
                                },
                                {
                                    "type": "text",
                                    "text": query
                                }
                            ]
                        }
                    ]
                )

                content = chat_response.choices[0].message.content
                
                logger.success("query_from_audio tool responded")
                return [{"audio_content": content}]
            except Exception as e:
                logger.error(f"query_from_audio error due to : {e} ")
                return [{"content":"technical error in mistral"}]
        @tool
        def sql_user_query_tool(user_query: str, file_path: str, table_name: str):
            """
            Answer a user's natural-language data question by generating and executing
            a schema-aware SQL query on a structured file using DuckDB.

            Use this tool when:
            - The user uploads a CSV or Excel file
            - The user asks a question in natural language (not raw SQL)
            - The answer requires querying the file using SQL semantics
            - Fast, in-memory analytics is sufficient

            Behavior:
            - Creates an in-memory DuckDB database
            - Loads CSV files using DuckDB's read_csv_auto
            - Loads Excel files using pandas and registers them as a DuckDB table
            - Extracts the table schema using DESCRIBE
            - Sends the schema, table name, and user question to an LLM
            - Parses and cleans the LLM-generated SQL
            - Executes the SQL query against DuckDB
            - Returns the query result as structured data

            Important:
            - The generated SQL MUST reference the provided `table_name`
            - The LLM is responsible for generating DuckDB-compatible SQL
            - Only CSV (.csv) and Excel (.xlsx) file formats are supported
            - The database exists only for the duration of this function call
            - No data is persisted to disk

            Args:
                user_query (str): Natural-language question from the user.
                file_path (str): Absolute or relative path to the uploaded file.
                table_name (str): Name of the DuckDB table created from the file.

            Returns:
                List[Dict]: Query results as a list of row dictionaries.
                Dict: Error information if any step fails (loading, SQL generation, or execution).
            """

            try:
                con = duckdb.connect(database=":memory:")
                
                logger.info("calling query from structured files tool!")
                if file_path.endswith(".csv"):
                    con.execute(f"""
                        CREATE TABLE {table_name} AS
                        SELECT * FROM read_csv_auto('{file_path}')
                    """)
                elif file_path.endswith(".xlsx"):
                    df = pd.read_excel(file_path)
                    con.register(table_name, df)
              
                schema = con.execute(f"DESCRIBE {table_name}").fetchall()
                table_schema="\n".join([f"{col[0]} ({col[1]})" for col in schema])
                response = self.llm.invoke(
                            template.format_messages(
                                table_name=table_name,
                                schema=table_schema,
                                user_query=user_query
                            )
                        )
                logger.info("SQL query generated!")
                sections=sql_utils.parse_llm_response(response.content)
                sql_query=sections["sql"]
                clean_query = sql_utils.clean_sql(sql_query)
                result = con.execute(clean_query).df()
               
                logger.success("query from structured files tool responded..")
                return result.to_dict(orient="records")
            except Exception as e:
                logger.error(f"error: {e}")
                return [{"content":"technical error in sql pre-processing"}]
            

        tools = [query_from_pdf, multimodal_tool, query_from_image,query_from_audio,sql_user_query_tool]
        return tools