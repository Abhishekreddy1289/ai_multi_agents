from pydantic import BaseModel
from typing import List, Dict
import uuid
import time
import numpy as np
from collections import defaultdict
import datetime
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path
import tempfile
from src.utils.pdf_processor import TextProcessor
from src.llm.indexing import Indexing

app = FastAPI(title="Chatbot")

os.environ["LANGSMITH_TRACING"] = "true"

class DeleteDocRequest(BaseModel):
    file_name: str

@app.post("/upload-doc")
async def upload_doc(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    tmp_path = None

    try:
        # 1️⃣ Save uploaded bytes to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # 2️⃣ Process PDF
        index_processor=Indexing(TextProcessor())
        message = index_processor.insert_doc(
            file_path=tmp_path,
            file_name=file.filename
        )

        return f"{file.filename} uploaded successfully"

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 3️⃣ Cleanup
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.post("/delete-doc")
async def delete_doc(request: DeleteDocRequest):
    try:
        # 2️⃣ Process PDF
        index_processor=Indexing(TextProcessor())
        message = index_processor.delete_doc(
            file_name=request.file_name
        )

        return f"{request.file_name} deleted successfully"

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

