from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class TextProcessor:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                "? ",
                "! ",
                ", ",
                " ",
                ""
            ],
        )

    def extract_text(self, file_path: str, file_name: str):
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        docs = []
        for i, doc in enumerate(documents):
            chunks = self.text_splitter.split_text(doc.page_content)

            for j, chunk in enumerate(chunks):
                docs.append({
                    "id": f"{file_name}-p{i+1}-c{j+1}",
                    "chunk_text": chunk,
                    "document_name": file_name
                })

        return docs

# from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parents[2]
# # src/utils/pdf_processor.py
# # parents[0] = utils
# # parents[1] = src
# # parents[2] = project_root

# pdf_path = BASE_DIR / "data" / "pdfs" / "Abhishek_V_S_.pdf"

# print("PDF path:", pdf_path)
# print("Exists:", pdf_path.exists())


# text_processor = TextProcessor()
# docs = text_processor.extract_text(
#     file_path=str(pdf_path),
#     file_name="Abhishek_V_S_"
# )
# print(docs)