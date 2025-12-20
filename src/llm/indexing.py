import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

import time
from pinecone import Pinecone
import sys
from pathlib import Path
from src.utils.pdf_processor import TextProcessor

from config import get_config
import os

cfg=get_config()

class Indexing:
    def __init__(self,text_processor : TextProcessor):
        self.pc=Pinecone(api_key=cfg["keys"]["pinecone_key"])
        self.index_name = "index1"
        self.namespace="namespace1"
        self.doc_processing=text_processor
        self.__call__()

    def __call__(self):
        if not self.pc.has_index (self.index_name):
            self.pc.create_index_for_model(
                name=self.index_name,
                region="us-east-1",
                cloud="aws",
                embed={
                    "model":"llama-text-embed-v2",
                    "field_map": {
                        "text":"chunk_text"
                    }
                }
            ) 
        # Wait for the index to be ready
        while not self.pc.describe_index(self.index_name).status['ready']:
            time.sleep(2)

    
    def insert_doc(self,file_path, file_name):
        index = self.pc.Index(self.index_name)
        records = []
        docs=self.doc_processing.extract_text(file_path, file_name)
        for doc in docs:
            records.append({
                "id": doc["id"],
                "chunk_text": doc["chunk_text"],
                "document_name": doc["document_name"]
            })
        
        index.upsert_records(
            records=records,
            namespace=self.namespace
        )
        time.sleep(10)
        return index.describe_index_stats()
    
    def delete_doc(self,file_name):
        index=self.pc.Index(self.index_name)
        index.delete(
            namespace=self.namespace,
            filter={
                "document_name":{
                    "$eq":file_name
                }
            }
        )
        time.sleep(5)
        return index.describe_index_stats()

    def delete_index(self):
        self.pc.delete_index(self.index_name)

        return f"Clean up Index"

# from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parents[2]

# pdf_path = BASE_DIR / "data" / "pdfs" / "Abhishek_V_S_.pdf"

# index_procoseer=Indexing(TextProcessor())
# results=index_procoseer.insert_doc(file_path=str(pdf_path),
#     file_name="Abhishek_V_S_")
# # results=index_procoseer.delete_doc("IITM Research Paper")
# print(results)