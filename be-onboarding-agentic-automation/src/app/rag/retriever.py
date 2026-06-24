import uuid
from dataclasses import dataclass

from sqlalchemy import select, text

from app.config import settings
from app.db import KnowledgeBaseChunk, KnowledgeBaseDocument, session_scope
from app.rag.embeddings import Embedder


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    section_title: str
    content: str
    vector_score: float
    lexical_score: float
    score: float

    @property
    def source_label(self) -> str:
        return f"{self.document_name} - {self.section_title}"


class RagRetriever:
    def __init__(self, embedder: Embedder) -> None:
        self._embedder = embedder

    def search(self, query: str, *, top_k: int | None = None) -> list[RetrievedChunk]:
        limit = top_k or settings.rag_top_k
        candidates = max(settings.rag_candidates, limit)
        query_embedding = self._embedder.embed_query(query)

        vector_rows = self._vector_search(query_embedding, candidates)
        lexical_rows = self._lexical_search(query, candidates)

        combined: dict[uuid.UUID, dict] = {}
        for rank, row in enumerate(vector_rows, start=1):
            entry = combined.setdefault(row.chunk_id, _entry(row))
            entry["vector_score"] = max(entry["vector_score"], row.vector_score)
            entry["rrf"] += _rrf(rank)

        for rank, row in enumerate(lexical_rows, start=1):
            entry = combined.setdefault(row.chunk_id, _entry(row))
            entry["lexical_score"] = max(entry["lexical_score"], row.lexical_score)
            entry["rrf"] += _rrf(rank)

        results = [
            RetrievedChunk(
                chunk_id=entry["chunk_id"],
                document_id=entry["document_id"],
                document_name=entry["document_name"],
                section_title=entry["section_title"],
                content=entry["content"],
                vector_score=entry["vector_score"],
                lexical_score=entry["lexical_score"],
                score=entry["rrf"],
            )
            for entry in combined.values()
        ]
        return sorted(results, key=lambda item: item.score, reverse=True)[:limit]

    def _vector_search(self, query_embedding: list[float], limit: int) -> list[RetrievedChunk]:
        with session_scope() as session:
            distance = KnowledgeBaseChunk.embedding.cosine_distance(query_embedding)
            rows = session.execute(
                select(KnowledgeBaseChunk, KnowledgeBaseDocument, distance.label("distance"))
                .join(KnowledgeBaseDocument, KnowledgeBaseDocument.id == KnowledgeBaseChunk.document_id)
                .order_by(distance)
                .limit(limit)
            ).all()

        results: list[RetrievedChunk] = []
        for chunk, document, distance_value in rows:
            vector_score = 1.0 - float(distance_value or 0.0)
            if vector_score < settings.rag_min_vector_score:
                continue
            results.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    document_name=document.original_filename,
                    section_title=chunk.section_title,
                    content=chunk.content,
                    vector_score=vector_score,
                    lexical_score=0.0,
                    score=0.0,
                )
            )
        return results

    def _lexical_search(self, query: str, limit: int) -> list[RetrievedChunk]:
        sql = text(
            """
            SELECT
                c.id AS chunk_id,
                c.document_id AS document_id,
                d.original_filename AS document_name,
                c.section_title AS section_title,
                c.content AS content,
                ts_rank_cd(
                    to_tsvector('simple', coalesce(c.section_title, '') || ' ' || c.content),
                    plainto_tsquery('simple', :query)
                ) AS lexical_score
            FROM kb_chunks c
            JOIN kb_documents d ON d.id = c.document_id
            WHERE to_tsvector('simple', coalesce(c.section_title, '') || ' ' || c.content)
                  @@ plainto_tsquery('simple', :query)
            ORDER BY lexical_score DESC
            LIMIT :limit
            """
        )
        with session_scope() as session:
            rows = session.execute(sql, {"query": query, "limit": limit}).mappings().all()

        return [
            RetrievedChunk(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                document_name=row["document_name"],
                section_title=row["section_title"],
                content=row["content"],
                vector_score=0.0,
                lexical_score=float(row["lexical_score"] or 0.0),
                score=0.0,
            )
            for row in rows
        ]


def _entry(row: RetrievedChunk) -> dict:
    return {
        "chunk_id": row.chunk_id,
        "document_id": row.document_id,
        "document_name": row.document_name,
        "section_title": row.section_title,
        "content": row.content,
        "vector_score": row.vector_score,
        "lexical_score": row.lexical_score,
        "rrf": 0.0,
    }


def _rrf(rank: int, *, k: int = 60) -> float:
    return 1.0 / (k + rank)
