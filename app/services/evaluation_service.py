# app/services/evaluation_service.py

import json
from app.services.embedding_service import get_embedding, cosine_similarity
from app.services.llm_service import call_llm

import json
import re

def safe_json_load(output: str):
    try:
        return json.loads(output)
    except:
        match = re.search(r'\{.*\}', output, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass

        # print("\nRAW LLM OUTPUT:\n", output)
        raise ValueError("Invalid JSON from LLM")

def evaluate_question(student, ideal, max_marks=5):

    # Step 1: similarity
    sim = cosine_similarity(
        get_embedding(student),
        get_embedding(ideal)
    )

    # Step 2: LLM scoring
    prompt = f"""
You are an exam evaluator.

Student Answer:
{student}

Ideal Answer:
{ideal}

Similarity Score: {sim}

Scoring Rules:
- Give score BETWEEN 0 and {max_marks}
- Ignore spelling mistakes if meaning is correct
- Focus on concept understanding

IMPORTANT:
- Ignore spelling mistakes if meaning is correct
- Focus on concept correctness
- Be fair, not overly strict

Return ONLY JSON:
{{
  "score": number,
  "feedback": "short explanation"
}}
"""

    raw_output = call_llm(prompt)
    # print("\n--- EVAL LLM OUTPUT ---\n", raw_output)
    llm_output = safe_json_load(raw_output)

    llm_score = llm_output["score"]
    sim_score = sim * max_marks

    # final score
    final_score = (0.6 * llm_score) + (0.4 * sim_score)

    return {
        "similarity": float(sim),
        "score": float(round(final_score, 2)),
        "max_marks": max_marks,
        "feedback": llm_output["feedback"]
    }