from pydantic import BaseModel
from typing import List, Optional


class QAItem(BaseModel):
    question: str
    answer: str


class ArticleInput(BaseModel):
    title: str
    content: str
    num_questions: Optional[int] = 3


class QAResponse(BaseModel):
    title: str
    qas: List[QAItem]
