import os
import uuid
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

VECTOR_DB_DIR = "data/chroma_db"
os.makedirs(VECTOR_DB_DIR, exist_ok=True)

# Initialize Embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Initialize Chroma Vector Store
vector_store = Chroma(
    collection_name="answer_keys",
    embedding_function=embeddings,
    persist_directory=VECTOR_DB_DIR
)

def store_answer_key(answer_key_id: str, parsed_key: list):
    """
    Stores an answer key in the vector store.
    parsed_key is a list of dicts: [{"question_id": "Q1", "question_text": "...", "ideal_answer": "...", "max_marks": 5}]
    """
    documents = []
    for item in parsed_key:
        content = f"Question: {item.get('question_text', '')}\nIdeal Answer: {item['ideal_answer']}"
        doc = Document(
            page_content=content,
            metadata={
                "answer_key_id": answer_key_id,
                "question_id": item["question_id"],
                "max_marks": item.get("max_marks", 5),
                "ideal_answer": item["ideal_answer"],
                "question_text": item.get("question_text", "")
            }
        )
        documents.append(doc)
    
    vector_store.add_documents(documents)
    return True

def get_answer_key(answer_key_id: str):
    """
    Retrieves all questions for a specific answer key using metadata filtering.
    """
    # Chroma doesn't have a simple "get all by metadata" without search, 
    # but we can do a search with a dummy query and high k, filtered by metadata.
    results = vector_store.similarity_search(
        query="", 
        k=100, 
        filter={"answer_key_id": answer_key_id}
    )
    return results

def list_answer_keys():
    """
    Returns a list of unique answer_key_ids stored in the vector store.
    """
    # Chroma get() returns all metadata
    data = vector_store.get(include=['metadatas'])
    metadatas = data.get('metadatas', [])
    unique_keys = set()
    for m in metadatas:
        if "answer_key_id" in m:
            unique_keys.add(m["answer_key_id"])
    return list(unique_keys)
