from functools import lru_cache

from fastapi import APIRouter, Query
from pydantic import BaseModel

from creo.agents.query import QueryAgent

router = APIRouter()


@lru_cache(maxsize=1)
def get_qa() -> QueryAgent:
    return QueryAgent()


class FAQResponse(BaseModel):
    answer: str
    sources: list[dict]
    confidence: str


@router.get("/ask", response_model=FAQResponse)
def ask_faq(question: str = Query(..., description="The creator's question"), category: str = Query(None, description="Optional category filter")):
    result = get_qa().answer(question, category=category)
    return FAQResponse(**result)


@router.get("/health")
def health():
    return {"status": "ok", "service": "faq"}
