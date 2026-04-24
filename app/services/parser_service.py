# app/services/parser_service.py

import json
from app.services.llm_service import call_llm
import re

def safe_json_load(output: str):
    try:
        return json.loads(output)
    except:
        # Try extracting JSON array
        match = re.search(r'\[.*\]', output, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass

        print("\nRAW LLM OUTPUT:\n", output)
        raise ValueError("LLM did not return valid JSON")

def parse_student_answers(ocr_text):

    prompt = f"""
This is OCR text from a handwritten answer sheet.

Your task:
- Identify each answer
- Assign correct question_id in order (Q1, Q2, Q3...)

IMPORTANT RULES:
- Even if numbering is missing, assume answers are in order
- First answer = Q1, second = Q2, etc.
- DO NOT assign all answers as Q1
- Each answer MUST have a unique question_id

STRICT OUTPUT:
- Return ONLY valid JSON
- No explanation
- No markdown

FORMAT:
[
  {{
    "question_id": "Q1",
    "student_answer": "..."
  }},
  {{
    "question_id": "Q2",
    "student_answer": "..."
  }}
]

TEXT:
{ocr_text}
"""
    output = call_llm(prompt)
    return safe_json_load(output)


def parse_answer_key(text):

    prompt = f"""
Extract:
- question_id
- question_text
- ideal_answer

IMPORTANT:
- Ensure each question has unique Q1, Q2, Q3...
- Maintain order

STRICT:
- Return ONLY JSON array
- No explanation
- No markdown
- No extra text

OUTPUT FORMAT:
[
  {{
    "question_id": "Q1",
    "question_text": "...",
    "ideal_answer": "..."
  }}
]

TEXT:
{text}
"""

    output = call_llm(prompt)
    return safe_json_load(output)