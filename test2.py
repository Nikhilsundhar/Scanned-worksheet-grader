import pytesseract
from PIL import Image
import pdfplumber
from groq import Groq
import json
import os

# ==============================
# CONFIG
# ==============================
GROQ_API_KEY =os.getenv("GROQ_API_KEY")
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

client = Groq(api_key=GROQ_API_KEY)

pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"


# ==============================
# 1. OCR → LLM (Answer Sheet)
# ==============================
def extract_student_answers(image_path):
    # Step 1: OCR
    img = Image.open(image_path)
    img=img.convert("L")  # grayscale
    ocr_text = pytesseract.image_to_string(img)

    print("\n--- OCR TEXT ---\n")
    print(ocr_text)

    # Step 2: LLM structuring
    prompt = f"""
This is OCR text from a handwritten answer sheet. 

Clean the text and extract:
- question_id
- student_answer

Normalize question numbers (1, q1, Q1 → Q1)

STRICT RULES:
- Output ONLY raw JSON
- Do NOT include explanations
- Do NOT use markdown or ``` blocks
- Do NOT include any text before or after JSON

Return ONLY valid JSON:
[
  {{
    "question_id": "Q1",
    "student_answer": "..."
  }}
]

TEXT:
{ocr_text}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    output = response.choices[0].message.content

    print("\n--- LLM OUTPUT ---\n")
    print(output)

    # Step 3: Parse JSON
    try:
        data = json.loads(output)
        return data
    except:
        print("\n⚠️ JSON parsing failed. Try refining prompt.")
        return None


# ==============================
# 2. PDF → LLM (Answer Key)
# ==============================
def extract_answer_key(pdf_path):
    # Step 1: Extract text from PDF
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    print("\n--- PDF TEXT ---\n")
    print(full_text)

    # Step 2: LLM structuring
    prompt = f"""
This is an answer key document.

Extract:
- question_id
- question_text (if available)
- ideal_answer

Normalize question numbers (1, q1, Q1 → Q1)
STRICT RULES:
- Output ONLY raw JSON
- Do NOT include explanations
- Do NOT use markdown or ``` blocks
- Do NOT include any text before or after JSON

Return ONLY valid JSON:
[
  {{
    "question_id": "Q1",
    "question_text": "...",
    "ideal_answer": "..."
  }}
]

TEXT:
{full_text}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    output = response.choices[0].message.content

    print("\n--- LLM OUTPUT ---\n")
    print(output)

    # Step 3: Parse JSON
    try:
        data = json.loads(output)
        return data
    except:
        print("\n⚠️ JSON parsing failed. Try refining prompt.")
        return None


# ==============================
# MAIN TEST
# ==============================
if __name__ == "__main__":
    # 🔁 change paths
    image_path = "C:/AI mini proj/AI-grader/files/correct_answers.png"
    pdf_path = "C:/AI mini proj/AI-grader/files/answer key.pdf"

    print("\n==============================")
    print("STUDENT ANSWER EXTRACTION")
    print("==============================")
    student_data = extract_student_answers(image_path)

    print("\n==============================")
    print("ANSWER KEY EXTRACTION")
    print("==============================")
    answer_key_data = extract_answer_key(pdf_path)

    print("\n==============================")
    print("FINAL OUTPUT")
    print("==============================")
    print("Student:", student_data)
    print("Answer Key:", answer_key_data)