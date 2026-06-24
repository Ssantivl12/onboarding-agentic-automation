import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import BigInteger, DateTime, Index, String, create_engine, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

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


_engine = None
_session_factory: sessionmaker[Session] | None = None


def init_db() -> None:
    if not settings.database_url:
        return

    Base.metadata.create_all(bind=_get_engine())


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


def _get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=_get_engine(), autoflush=False, expire_on_commit=False)
    return _session_factory
