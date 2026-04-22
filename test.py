import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# -------- ANSWER KEY -------- #

answer_key = {
    "Q1": "The basic unit of life is the cell. It is the smallest structural and functional unit of all living organisms.",
    "Q2": "Photosynthesis is the process by which green plants use sunlight, carbon dioxide, and water to produce glucose and oxygen.",
    "Q3": "The mitochondria is responsible for energy production in the cell and generates ATP through respiration.",
    "Q4": "DNA is the genetic material that carries hereditary information and determines traits.",
    "Q5": "The heart pumps blood throughout the body and supplies oxygen and nutrients while removing waste.",
    "Q6": "An ecosystem is a community of living organisms interacting with each other and their environment.",
    "Q7": "Respiration is the process by which cells break down food to release energy.",
    "Q8": "Enzymes are biological catalysts that speed up chemical reactions.",
    "Q9": "Natural selection is the process where organisms with favorable traits survive and reproduce.",
    "Q10": "Chlorophyll is a green pigment that absorbs sunlight for photosynthesis."
}

# -------- RAW ANSWER SHEET -------- #

answer_sheet = """
Q1.
Tissue is the basic unit of life. It is made up of many organs and controls body functions.

Q2.
Photosynthesis is the process where plants breathe in oxygen and release carbon dioxide.

Q3.
The nucleus is responsible for producing energy in the cell and controlling power.

Q4.
DNA is a type of protein that helps in digestion of food in the body.

Q5.
The heart helps in digestion by breaking down food in the stomach.

Q6.
Ecosystem includes only non-living things like air, water, and soil.

Q7.
Respiration is the process by which plants make their food using sunlight.

Q8.
Enzymes are substances that store energy in the body for later use.

Q9.
Natural selection means all organisms survive equally in nature.Q1.
Tissue is the basic unit of life. It is made up of many organs and controls body functions.

Q10.
Chlorophyll stores oxygen inside the plant and releases it when needed.
 
"""

# -------- STEP 1: SPLIT ANSWERS -------- #

import re

def split_answers(text):
    # match Q1, Q1., 1., 1), etc.
    pattern = r"(?:Q\s*)?(\d+)[\).\s]"
    
    matches = list(re.finditer(pattern, text))
    
    answers = {}
    
    for i, match in enumerate(matches):
        q_num = match.group(1)
        start = match.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        
        answer = text[start:end].strip()
        answers[f"Q{q_num}"] = answer
    
    return answers

student_answers = split_answers(answer_sheet)
print(student_answers)

# -------- STEP 2: SIMILARITY -------- #

def similarity(a, b):
    emb1 = model.encode([a])
    emb2 = model.encode([b])
    return cosine_similarity(emb1, emb2)[0][0]

# -------- STEP 3: SCORING -------- #

def sim_to_score(sim):
    if sim > 0.85:
        return 5
    elif sim > 0.70:
        return 3
    elif sim > 0.55:
        return 1
    else:
        return 0

# -------- RUN -------- #

total_score = 0

for q in answer_key:
    student_ans = student_answers.get(q, "")
    key_ans = answer_key[q]
    
    sim = similarity(key_ans, student_ans)
    score = sim_to_score(sim)
    
    total_score += score
    
    print(f"\n{q}")
    print(f"Similarity: {sim:.3f}")
    print(f"Score: {score}/5")

print("\n====================")
print(f"TOTAL SCORE: {total_score}/50")