import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

from fastapi import HTTPException
from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text, create_engine, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


class KnowledgeBaseDocument(Base):
    __tablename__ = "kb_documents"
    __table_args__ = (
        Index("idx_kb_documents_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    stored_filename: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String, nullable=False)
    pdf_path: Mapped[str] = mapped_column(String, nullable=False)
    markdown_path: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ready")
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    chunks: Mapped[list["KnowledgeBaseChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class KnowledgeBaseChunk(Base):
    __tablename__ = "kb_chunks"
    __table_args__ = (
        Index("idx_kb_chunks_document_id", "document_id"),
        Index("idx_kb_chunks_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kb_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    section_title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dimensions), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    document: Mapped[KnowledgeBaseDocument] = relationship(back_populates="chunks")


_engine = None
_session_factory: sessionmaker[Session] | None = None


def init_db() -> None:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required for the full RAG backend.")

    engine = _get_engine()
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    except Exception as exc:
        raise RuntimeError("Postgres extension 'vector' is required. Install/enable pgvector.") from exc

    Base.metadata.create_all(bind=engine)
    _create_rag_indexes(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = _get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _get_engine():
    global _engine
    if _engine is None:
        if not settings.database_url:
            raise HTTPException(
                status_code=503,
                detail="DATABASE_URL is required for knowledge-base document management.",
            )
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def _create_rag_indexes(engine) -> None:
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_kb_chunks_fts
                    ON kb_chunks
                    USING GIN (
                        to_tsvector('simple', coalesce(section_title, '') || ' ' || content)
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding_cosine
                    ON kb_chunks
                    USING hnsw (embedding vector_cosine_ops)
                    """
                )
            )
    except Exception as exc:
        raise RuntimeError("Could not create RAG search indexes for kb_chunks.") from exc


def _get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=_get_engine(), autoflush=False, expire_on_commit=False)
    return _session_factory
