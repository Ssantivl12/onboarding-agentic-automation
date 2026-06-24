from pydantic import BaseModel, Field
from fastapi import APIRouter

from app.config import settings
from app.rag.retriever import RagRetriever

router = APIRouter(prefix="/rag", tags=["rag"])
_retriever: RagRetriever | None = None


def set_retriever(retriever: RagRetriever) -> None:
    global _retriever
    _retriever = retriever


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


class RagSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    section_title: str
    content: str
    vector_score: float
    lexical_score: float
    score: float


@router.post("/search", response_model=list[RagSearchResult])
def search(req: RagSearchRequest) -> list[RagSearchResult]:
    assert _retriever is not None, "RAG retriever not initialized"
    top_k = req.top_k or settings.rag_top_k
    return [
        RagSearchResult(
            chunk_id=str(chunk.chunk_id),
            document_id=str(chunk.document_id),
            document_name=chunk.document_name,
            section_title=chunk.section_title,
            content=chunk.content,
            vector_score=chunk.vector_score,
            lexical_score=chunk.lexical_score,
            score=chunk.score,
        )
        for chunk in _retriever.search(req.query, top_k=top_k)
    ]
