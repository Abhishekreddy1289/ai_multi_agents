from pathlib import Path
import sys
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

    def __call__(self):

        @tool
        def web_search(query: str):
            """
            Perform a real-time web search for the given query.

            Use this tool when the question requires:
            - Recent or up-to-date information
            - News, current events, or live data
            - Information not present in the local knowledge base

            Args:
                query (str): The search query.

            Returns:
                List[Dict]: A list of search result entries with raw content.
            """
            try:
                logger.info("calling web search tool")
                search = TavilySearch(max_results=3, include_raw_content=True)
                search_results = search.run(query)
                logger.success("web_search tool responded")
                return search_results["results"]
            except Exception as e:
                logger.error(f"web_search error due to : {e} ")
                return [{"content":"technical error in web search"}]

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


        tools = [query_from_pdf, web_search, query_from_image,query_from_audio]
        return tools