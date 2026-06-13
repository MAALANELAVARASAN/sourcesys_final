from pydantic import BaseModel
from typing import Literal, Optional


class UnifiedFAQRequest(BaseModel):
    prompt: str
    filename: Optional[str] = None
    content: Optional[str] = None


class FAQPair(BaseModel):
    question: str
    answer: str


class FAQResponse(BaseModel):
    source: Literal["knowledge_base", "ai_knowledge"]
    direct_answer: str          # answers the prompt directly
    faq_pairs: list[FAQPair]
    total: int