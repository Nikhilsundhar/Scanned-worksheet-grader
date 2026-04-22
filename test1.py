import re
import json
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
import os

# ---------------- CONFIG ---------------- #
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

llm = genai.GenerativeModel("gemini-2.5-flash")

embed_model = SentenceTransformer('all-MiniLM-L6-v2')

# ---------------- ANSWER KEY ---------------- #

answer_key = {
    "Q1": "The basic unit of life is the cell. It is the smallest structural and functional unit of all living organisms.",
    "Q2": "Photosynthesis is the process by which green plants use sunlight, carbon dioxide, and water to produce glucose and oxygen."
}

# ---------------- STUDENT ANSWERS ---------------- #

student_answers = {
    "Q1": "Cell is the basic unit of life. It is very small and found in all living organisms.",
    "Q2": "Plants make food using sunlight and give oxygen."
}

# ---------------- HELPERS ---------------- #

def get_embedding_similarity(a, b):
    emb1 = embed_model.encode([a])
    emb2 = embed_model.encode([b])
    return cosine_similarity(emb1, emb2)[0][0]

def clean_json(text):
    text = text.strip()
    text = text.replace("```json", "").replace("```", "")
    return json.loads(text)

# ---------------- STEP 1: EXTRACT CONCEPTS ---------------- #

def extract_concepts(answer):
    prompt = f"""
    Extract key concepts required to correctly answer this.

    Answer:
    {answer}

    Return ONLY JSON:
    {{
      "concepts": ["...", "..."]
    }}
    """

    response = llm.generate_content(prompt)
    return clean_json(response.text)["concepts"]

# ---------------- STEP 2: CONCEPT COVERAGE ---------------- #

def evaluate_concepts(concepts, student_answer):
    prompt = f"""
    You are grading a student answer.

    Required concepts:
    {concepts}

    Student Answer:
    {student_answer}

    For each concept classify as:
    - present
    - partially_present
    - missing

    Return ONLY JSON:
    {{
      "evaluation": [
        {{"concept": "...", "status": "..."}}
      ]
    }}
    """

    response = llm.generate_content(prompt)
    return clean_json(response.text)["evaluation"]

# ---------------- SCORING ---------------- #

def concept_score(evaluation):
    score = 0
    for item in evaluation:
        if item["status"] == "present":
            score += 1
        elif item["status"] == "partially_present":
            score += 0.5
    return score

def similarity_to_score(sim):
    return sim * 5  # normalize

# ---------------- MAIN ---------------- #

concept_cache = {}

total_score = 0

for q in answer_key:
    print(f"\n🔹 {q}")

    key_ans = answer_key[q]
    student_ans = student_answers[q]

    # --- Step 1: get concepts (cached) ---
    if q not in concept_cache:
        concept_cache[q] = extract_concepts(key_ans)

    concepts = concept_cache[q]

    # --- Step 2: concept evaluation ---
    evaluation = evaluate_concepts(concepts, student_ans)
    c_score = concept_score(evaluation)

    # --- Step 3: embedding ---
    sim = get_embedding_similarity(key_ans, student_ans)
    e_score = similarity_to_score(sim)

    # --- Step 4: combine ---
    final = 0.6 * c_score + 0.4 * e_score

    total_score += final

    print(f"Concept Score: {c_score:.2f}")
    print(f"Embedding Score: {e_score:.2f}")
    print(f"Final Score: {final:.2f}/5")

print("\n====================")
print(f"TOTAL SCORE: {total_score:.2f}")