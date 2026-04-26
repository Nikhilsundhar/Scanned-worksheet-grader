# app/services/evaluation_service.py

import json
import re
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.services.llm_service import llm
from app.services.vector_store_service import embeddings, get_answer_key
import numpy as np

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))



def evaluate_question(student_answer, ideal_answer, max_marks=5):
    # Step 1: similarity
    student_emb = embeddings.embed_query(student_answer)
    ideal_emb = embeddings.embed_query(ideal_answer)
    sim = cosine_similarity(student_emb, ideal_emb)

    # Step 2: LLM scoring via LangChain LCEL
    prompt_template = PromptTemplate(
        input_variables=["student", "ideal", "sim", "max_marks"],
        template="""
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

Return ONLY JSON:
{{
  "score": number,
  "feedback": "short explanation"
}}
"""
    )
    
    chain = prompt_template | llm | JsonOutputParser()
    
    try:
        llm_output = chain.invoke({
            "student": student_answer,
            "ideal": ideal_answer,
            "sim": sim,
            "max_marks": max_marks
        })
    except Exception as e:
        print("LCEL parsing failed:", e)
        llm_output = {"score": 0, "feedback": "Error parsing LLM response"}

    llm_score = llm_output.get("score", 0)
    sim_score = sim * max_marks

    # final score
    final_score = (0.6 * llm_score) + (0.4 * sim_score)

    return {
        "similarity": float(sim),
        "score": float(round(final_score, 2)),
        "max_marks": max_marks,
        "feedback": llm_output.get("feedback", "")
    }

def evaluate_student_sheet(answer_key_id: str, student_answers: list):
    """
    Evaluates a list of student answers against the Answer Key in the Vector Store.
    """
    results = []
    total_score = 0
    total_max = 0

    # Retrieve answer key from vector store
    key_docs = get_answer_key(answer_key_id)
    key_map = {doc.metadata["question_id"]: doc for doc in key_docs}

    for ans in student_answers:
        qid = ans.get("question_id")
        student_ans_text = ans.get("student_answer", "")

        if qid in key_map:
            ideal_ans = key_map[qid].metadata["ideal_answer"]
            max_marks = key_map[qid].metadata.get("max_marks", 5)

            res = evaluate_question(
                student_answer=student_ans_text,
                ideal_answer=ideal_ans,
                max_marks=max_marks
            )

            total_score += res["score"]
            total_max += max_marks

            results.append({
                "question_id": qid,
                **res
            })
    
    percentage = round((total_score / total_max) * 100, 2) if total_max > 0 else 0.0

    return {
        "total_score": round(total_score, 2),
        "total_max_marks": total_max,
        "percentage": percentage,
        "results": results
    }