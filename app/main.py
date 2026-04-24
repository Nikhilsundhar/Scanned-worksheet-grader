from fastapi import FastAPI, UploadFile, File
import os
import uuid
import shutil

from app.services.ocr_service import extract_text_from_image
from app.services.pdf_service import extract_text_from_pdf
from app.services.parser_service import parse_student_answers, parse_answer_key
from app.services.evaluation_service import evaluate_question
from app.models.schemas import EvaluationRequest

app = FastAPI()

# ==============================
# CREATE FOLDERS (IMPORTANT)
# ==============================
BASE_DIR = "data"
ANSWER_KEY_DIR = os.path.join(BASE_DIR, "answer_keys")
STUDENT_DIR = os.path.join(BASE_DIR, "student_sheets")

os.makedirs(ANSWER_KEY_DIR, exist_ok=True)
os.makedirs(STUDENT_DIR, exist_ok=True)


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
# PARSE STUDENT ANSWER SHEET
# ==============================
@app.post("/parse-student/")
async def parse_student(file: UploadFile = File(...)):

    path = save_file(file, "student")

    # OCR
    text = extract_text_from_image(path)

    # LLM parsing
    result = parse_student_answers(text)

    return {
        "file_path": path,
        "parsed_data": result
    }


# ==============================
# PARSE ANSWER KEY (PDF)
# ==============================
@app.post("/parse-answer-key/")
async def parse_answer_key_api(file: UploadFile = File(...)):

    path = save_file(file, "answer_key")

    # Extract text
    text = extract_text_from_pdf(path)

    # LLM parsing
    result = parse_answer_key(text)

    return {
        "file_path": path,
        "parsed_data": result
    }


# ==============================
# EVALUATE (CORE)
# ==============================
@app.post("/evaluate/")
async def evaluate(req:EvaluationRequest):

    # Map answer key by question_id
    key_map = {q.question_id: q for q in req.answer_key}

    results = []

    total_score = 0
    total_max = 0

    for ans in req.student_answers:
        qid = ans.question_id

        if qid in key_map:
            res = evaluate_question(
                ans.student_answer,
                key_map[qid].ideal_answer,
                key_map[qid].max_marks
            )

            total_score += res["score"]
            total_max += key_map[qid].max_marks

            results.append({
                "question_id": qid,
                **res
            })

    return {
        "total_score": round(total_score, 2),
        "total_max_marks": total_max,
        "percentage": round((total_score / total_max) * 100, 2),
        "results": results
}