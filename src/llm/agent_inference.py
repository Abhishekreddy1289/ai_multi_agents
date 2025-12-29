import sys
from pathlib import Path
import  streamlit as st
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from langchain_mistralai import ChatMistralAI
from langchain.agents import create_agent
from src.llm.tools import Tools
from langchain.messages import HumanMessage,SystemMessage
from src.prompts import get_prompt

from config import get_config
import os

cfg=get_config()
os.environ["MISTRAL_API_KEY"]=cfg["keys"]["mistral_api_key"]
os.environ["LANGSMITH_API_KEY"] = cfg["keys"]["langsmith_api_key"]
os.environ["LANGSMITH_TRACING"] = "true"

class CreateAgent:
    def __init__(self):
        self.tools = Tools().__call__()
        self.model = ChatMistralAI(
            model=cfg["models"]["mistral_chat_model"], temperature=0, max_retries=1
        )
        self.agent = create_agent(model=self.model, tools=self.tools)

    def query_inference(self, query,system_prompt_type, image_path=None, audio_path=None, pdf_path=None, csv_path=None, xlsx_path=None, table_name=None,  filename=None):
        system_prompt = get_prompt(system_prompt_type.lower())  # or "friendly" / "expert"
        st.toast("Inference Started!",icon="🎉")
        messages = [SystemMessage(content=system_prompt)]

        if image_path:
            messages.append(HumanMessage(content=f"Image Path: {image_path}"))
        if audio_path:
            messages.append(HumanMessage(content=f"Audio Path: {audio_path}"))
        if pdf_path:
            file_info = f"PDF Path: {pdf_path}"
            if filename:
                file_info += f" and filename: {filename}"
            messages.append(HumanMessage(content=file_info))
        if csv_path:
            file_info = f"CSV Path: {csv_path} and Table Name: {table_name}"
            print(file_info)
            messages.append(HumanMessage(content=file_info))
        if xlsx_path:
            file_info = f"Excel Path: {xlsx_path} and Table Name: {table_name}"
            print(file_info)
            messages.append(HumanMessage(content=file_info))

        messages.append(HumanMessage(content=query))

        response = self.agent.invoke({"messages": messages})
        return response["messages"][-1].content
