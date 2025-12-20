# chainlit_app.py
import os
import tempfile
from pathlib import Path
import chainlit as cl
from src.llm.agent_inference import CreateAgent

# Initialize agent once
agent = CreateAgent()
os.environ["LANGSMITH_TRACING"] = "true"

def detect_attachment_type(file: Path) -> str:
    ext = file.suffix.lower()
    if ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]:
        return "image"
    if ext in [".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"]:
        return "audio"
    if ext == ".pdf":
        return "pdf"
    return "unknown"

async def save_temp_file(file: cl.File) -> Path:
    """Save uploaded file to a temporary path"""
    suffix = Path(file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        return Path(tmp.name)

# Handle text messages
@cl.on_message
async def handle_message(message: cl.Message):
    query = message.content
    if not query.strip():
        await cl.Message(content="❌ Empty message").send()
        return

    response = agent.query_inference(query)
    await cl.Message(content=response, markdown=True).send()

# Handle uploaded files
@cl.on_file_upload
async def handle_file_upload(file: cl.File):
    temp_path = await save_temp_file(file)
    attachment_type = detect_attachment_type(temp_path)

    try:
        if attachment_type == "unknown":
            await cl.Message(content="❌ Unsupported attachment type", markdown=True).send()
            return

        if attachment_type == "pdf":
            response = agent.pdf_inference(query="", pdf_path=temp_path, filename=file.name)
            await cl.Message(content=response, markdown=True).send()

        elif attachment_type == "image":
            response = agent.image_inference(query="", image_path=temp_path)
            await cl.Message(content=response, markdown=True).send()
            await cl.Message(content=str(temp_path), type="image").send()

        elif attachment_type == "audio":
            response = agent.audio_inference(query="", audio_path=temp_path)
            await cl.Message(content=response, markdown=True).send()
            await cl.Message(content=str(temp_path), type="audio").send()

    finally:
        if temp_path.exists():
            temp_path.unlink()
