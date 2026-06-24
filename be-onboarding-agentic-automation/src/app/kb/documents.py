import hashlib
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import desc, select

from app.config import settings
from app.db import KnowledgeBaseDocument, session_scope
from app.kb.converter import convert_to_markdown
from app.kb.loader import clear_cache_for


@dataclass(frozen=True)
class StoredKnowledgeBaseDocument:
    id: uuid.UUID
    original_filename: str
    stored_filename: str
    content_type: str
    size_bytes: int
    sha256: str
    pdf_path: Path
    markdown_path: Path


def list_documents() -> list[dict]:
    with session_scope() as session:
        rows = session.scalars(
            select(KnowledgeBaseDocument).order_by(desc(KnowledgeBaseDocument.created_at))
        ).all()
        return [_document_to_dict(row) for row in rows]


def create_document(
    *,
    original_filename: str,
    content_type: str,
    content: bytes,
) -> StoredKnowledgeBaseDocument:
    doc_id = uuid.uuid4()
    upload_dir = settings.resolved_kb_upload_dir
    kb_dir = settings.kb_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    kb_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _safe_filename(original_filename)
    suffix = Path(safe_name).suffix.lower() or ".pdf"
    if suffix != ".pdf" or content_type.lower() != "application/pdf":
        raise ValueError("Only PDF files are supported.")

    stem = Path(safe_name).stem
    stored_filename = f"{stem}-{doc_id.hex[:8]}{suffix}"
    markdown_filename = f"{stem}-{doc_id.hex[:8]}.md"
    source_path = upload_dir / stored_filename
    markdown_path = kb_dir / markdown_filename

    max_bytes = settings.kb_max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise ValueError(f"PDF exceeds {settings.kb_max_upload_mb} MB.")

    try:
        source_path.write_bytes(content)
        markdown = convert_to_markdown(source_path, original_filename, content_type)
        markdown_path.write_text(markdown, encoding="utf-8")
        sha256 = hashlib.sha256(content).hexdigest()

        document = StoredKnowledgeBaseDocument(
            id=doc_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            content_type=content_type,
            size_bytes=len(content),
            sha256=sha256,
            pdf_path=source_path,
            markdown_path=markdown_path,
        )
        _insert_document(document)
        return document
    except Exception:
        _unlink_if_exists(source_path)
        _unlink_if_exists(markdown_path)
        raise


def delete_document(document_id: uuid.UUID) -> bool:
    with session_scope() as session:
        document = session.get(KnowledgeBaseDocument, document_id)
        if document is None:
            return False

        pdf_path = Path(document.pdf_path)
        markdown_path = Path(document.markdown_path)
        session.delete(document)

    _unlink_if_exists(pdf_path)
    _unlink_if_exists(markdown_path)
    clear_cache_for(markdown_path)
    return True


def _insert_document(document: StoredKnowledgeBaseDocument) -> None:
    with session_scope() as session:
        session.add(
            KnowledgeBaseDocument(
                id=document.id,
                original_filename=document.original_filename,
                stored_filename=document.stored_filename,
                content_type=document.content_type,
                size_bytes=document.size_bytes,
                sha256=document.sha256,
                pdf_path=str(document.pdf_path),
                markdown_path=str(document.markdown_path),
                status="ready",
            )
        )


def _safe_filename(filename: str) -> str:
    name = Path(filename).name.strip() or "document.pdf"
    stem = Path(name).stem
    suffix = Path(name).suffix
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip(".-") or "document"
    safe_suffix = re.sub(r"[^A-Za-z0-9.]+", "", suffix)[:12]
    return f"{safe_stem}{safe_suffix}"


def _unlink_if_exists(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _document_to_dict(document: KnowledgeBaseDocument) -> dict:
    return {
        "id": document.id,
        "original_filename": document.original_filename,
        "stored_filename": document.stored_filename,
        "content_type": document.content_type,
        "size_bytes": document.size_bytes,
        "sha256": document.sha256,
        "pdf_path": document.pdf_path,
        "markdown_path": document.markdown_path,
        "status": document.status,
        "error": document.error,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
    }
