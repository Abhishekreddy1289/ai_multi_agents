# streamlit_app.py
import os
import tempfile
from pathlib import Path
from io import BytesIO
import time

import streamlit as st
from src.llm.agent_inference import CreateAgent
from src.utils.log import AppLogger
logger = AppLogger.setup()


# --- Blue theme CSS ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #1E90FF;  /* DodgerBlue */
        color: white;
    }
    .css-1d391kg {  
        background-color: #1C86EE;
    }
    .stButton>button {
        background-color: #104E8B;
        color: white;
    }
    .stTextInput>div>input {
        background-color: #ADD8E6;
        color: black;
    }
    .stChatMessage>div {
        color: black;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Page config
st.set_page_config(page_title="🤖 Advanced Multimodal Chatbot", layout="wide")
st.title("🤖 Advanced Multimodal Chatbot")
st.markdown("You can send **text, PDF, image, or audio** files and get responses with markdown formatting.")
logger.info("Streamlit Running...")


# Initialize agent
agent = CreateAgent()
os.environ["LANGSMITH_TRACING"] = "true"

st.sidebar.header("Assistant Settings")

selected_prompt_type = st.sidebar.radio(
    "Select Assistant Style",
    options=["Default", "Friendly", "Technical"],
    index=0  # Default selected
)

if "system_prompt_type" not in st.session_state:
    st.session_state.system_prompt_type = "Default"

# Update system prompt when user changes selection
st.session_state.system_prompt_type = selected_prompt_type


# --------------------------
# Session states
# --------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --------------------------
# Helper functions
# --------------------------
def detect_attachment_type(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    if ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]:
        return "image"
    if ext in [".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"]:
        return "audio"
    if ext == ".pdf":
        return "pdf"
    return "unknown"

def save_temp_file(file) -> Path:
    suffix = Path(file.name).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(file.read())
    tmp.close()
    return Path(tmp.name)

def process_input(prompt, uploaded_file=None):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    logger.info(f"Inference Starting")
    temp_path = None
    response = ""
    try:
        file_args = {"image_path": None, "audio_path": None, "pdf_path": None, "filename": None}
        if uploaded_file:
            temp_path = save_temp_file(uploaded_file)
            attachment_type = detect_attachment_type(temp_path)

            if attachment_type == "unknown":
                st.error("Unsupported attachment type.")
                logger.error(f"Unsupported attachment type.")
            elif attachment_type == "pdf":
                file_args["pdf_path"] = temp_path
                file_args["filename"] = uploaded_file.name
            elif attachment_type == "image":
                file_args["image_path"] = temp_path
            elif attachment_type == "audio":
                file_args["audio_path"] = temp_path

        logger.info(f" Temp File Path: {file_args}")
        # Single inference call handling all types
        response = agent.query_inference(prompt,system_prompt_type=st.session_state.system_prompt_type, **file_args)
        logger.success("Inference Completed")
        with st.chat_message("assistant"):
            st.markdown(response)

    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()
    
    st.session_state.chat_history.append({"role": "assistant", "content": response})



# --------------------------
# Sidebar: File upload
# --------------------------
st.sidebar.header("Upload Attachment (Optional)")
uploaded_file = st.sidebar.file_uploader(
    "Choose a file", 
    type=["pdf","png","jpg","jpeg","webp","bmp","tiff","wav","mp3","m4a","aac","flac","ogg"]
)

# --------------------------
# Display chat history
# --------------------------
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Recommended questions
recommended_questions = [
    "What does LLM stand for and how does it function?",
    "What are LLM agents and how do they work?",
    "What is the difference between LLMs and LLM agents?"
]

if not st.session_state.chat_history:
    st.write("**Recommended Questions:**")
    cols = st.columns(len(recommended_questions))
    for i, question in enumerate(recommended_questions):
        if cols[i].button(question):
            process_input(question, uploaded_file=None)

# --------------------------
# Chat input
# --------------------------
if query := st.chat_input("Ask your question here:"):
    process_input(query, uploaded_file=uploaded_file)
