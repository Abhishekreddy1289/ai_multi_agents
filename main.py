from pydantic import BaseModel
from typing import Optional
import os
from pathlib import Path
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from src.utils.pdf_processor import TextProcessor
from src.llm.indexing import Indexing
from src.llm.agent_inference import CreateAgent

app = FastAPI(title="Chatbot")

os.environ["LANGSMITH_TRACING"] = "true"

agent = CreateAgent()  # 🔥 Initialize agent once


from pathlib import Path
from fastapi import UploadFile

def detect_attachment_type(file: UploadFile) -> str:
    ext = Path(file.filename).suffix.lower()

    if ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]:
        return "image"

    if ext in [".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"]:
        return "audio"

    if ext == ".pdf":
        return "pdf"

    return "unknown"



async def save_temp_file(file: UploadFile) -> str:
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        return tmp.name


@app.post("/conversation")
async def conversation(
    query: Optional[str] = Form(None),
    attachment: Optional[UploadFile] = File(None)
):
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    temp_path = None

    try:
        # ---------- NO ATTACHMENT → TEXT ONLY ----------
        if not attachment:
            response = agent.query_inference(query)
            return {
                "query": query,
                "attachment": None,
                "response": response
            }

        # ---------- ATTACHMENT PRESENT ----------
        attachment_type = detect_attachment_type(attachment)

        if attachment_type == "unknown":
            raise HTTPException(status_code=400, detail="Unsupported attachment type")

        temp_path = await save_temp_file(attachment)

        # ---------- PDF ----------
        if attachment_type == "pdf":
            response = agent.pdf_inference(
                query=query,
                pdf_path=temp_path,
                filename=attachment.filename
            )

        # ---------- IMAGE ----------
        elif attachment_type == "image":
            response = agent.image_inference(
                query=query,
                image_path=temp_path
            )

        # ---------- AUDIO ----------
        elif attachment_type == "audio":
            response = agent.audio_inference(
                query=query,
                audio_path=temp_path
            )

        return {
            "query": query,
            "attachment": {
                "filename": attachment.filename,
                "type": attachment_type
            },
            "response": response
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
