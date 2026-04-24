from pydantic import BaseModel
from typing import List

class AnswerKeyItem(BaseModel):
    question_id: str
    ideal_answer: str
    max_marks: int


class StudentAnswerItem(BaseModel):
    question_id: str
    student_answer: str


class EvaluationRequest(BaseModel):
    answer_key: List[AnswerKeyItem]
    student_answers: List[StudentAnswerItem]