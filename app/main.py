#main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import shutil

from app.services.pdf_service import extract_text_from_pdf
from app.services.parser_service import parse_student_answers_from_image, parse_answer_key
from app.services.evaluation_service import evaluate_student_sheet
from app.services.vector_store_service import store_answer_key, list_answer_keys

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# CREATE FOLDERS
# ==============================
BASE_DIR = "data"
ANSWER_KEY_DIR = os.path.join(BASE_DIR, "answer_keys")
STUDENT_DIR = os.path.join(BASE_DIR, "student_sheets")
STATIC_DIR = os.path.join("app", "static")

os.makedirs(ANSWER_KEY_DIR, exist_ok=True)
os.makedirs(STUDENT_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        return {"message": "UI not built yet."}
    return FileResponse(index_path)

# ==============================
# FILE SAVE HELPER
# ==============================
def save_file(file: UploadFile, file_type="student"):
    safe_name = os.path.basename(file.filename)
    unique_name = f"{uuid.uuid4()}_{safe_name}"

    if file_type == "answer_key":
        path = os.path.join(ANSWER_KEY_DIR, unique_name)
    else:
        path = os.path.join(STUDENT_DIR, unique_name)

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return path

# ==============================
# API: UPLOAD & STORE ANSWER KEY
# ==============================
@app.post("/api/upload-answer-key/")
async def api_upload_answer_key(
    file: UploadFile = File(...),
    answer_key_id: str = Form(...)
):
    path = save_file(file, "answer_key")
    text = extract_text_from_pdf(path)
    parsed_data = parse_answer_key(text)
    
    # Store in Vector Store
    store_answer_key(answer_key_id, parsed_data)

    return {
        "status": "success",
        "answer_key_id": answer_key_id,
        "parsed_questions_count": len(parsed_data)
    }

# ==============================
# API: LIST ANSWER KEYS
# ==============================
@app.get("/api/answer-keys/")
async def api_list_answer_keys():
    keys = list_answer_keys()
    return {"answer_keys": keys}

from typing import List

# ==============================
# API: EVALUATE STUDENT SHEET
# ==============================
@app.post("/api/evaluate/{answer_key_id}")
async def api_evaluate(answer_key_id: str, files: List[UploadFile] = File(...)):
    # Check if answer key exists
    keys = list_answer_keys()
    if answer_key_id not in keys:
        raise HTTPException(status_code=404, detail="Answer key not found")

    student_answers_combined = []

    for file in files:
        path = save_file(file, "student")
        
        # LLM parsing (now accepts image path directly)
        student_answers = parse_student_answers_from_image(path)
        
        if isinstance(student_answers, list):
            student_answers_combined.extend(student_answers)

    # Evaluate using Vector Store + LangChain LCEL
    evaluation_result = evaluate_student_sheet(answer_key_id, student_answers_combined)

    return {
        "status": "success",
        "evaluation": evaluation_result
    }