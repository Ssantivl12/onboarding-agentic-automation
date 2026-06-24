import uuid
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.kb.converter import UnsupportedKnowledgeBaseFile
from app.kb.documents import create_document, delete_document, list_documents

router = APIRouter(prefix="/kb", tags=["knowledge-base"])


class KnowledgeBaseDocument(BaseModel):
    id: uuid.UUID
    original_filename: str
    stored_filename: str
    content_type: str
    size_bytes: int
    sha256: str
    pdf_path: str
    markdown_path: str
    status: str = "ready"
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@router.get("/documents", response_model=list[KnowledgeBaseDocument])
def get_documents() -> list[dict]:
    return list_documents()


@router.post(
    "/documents",
    response_model=KnowledgeBaseDocument,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(file: UploadFile = File(...)) -> dict:
    if (file.content_type or "").lower() != "application/pdf":
        raise HTTPException(status_code=415, detail="Only PDF files are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        document = create_document(
            original_filename=file.filename or "document.pdf",
            content_type=file.content_type or "application/octet-stream",
            content=content,
        )
    except UnsupportedKnowledgeBaseFile as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "id": document.id,
        "original_filename": document.original_filename,
        "stored_filename": document.stored_filename,
        "content_type": document.content_type,
        "size_bytes": document.size_bytes,
        "sha256": document.sha256,
        "pdf_path": str(document.pdf_path),
        "markdown_path": str(document.markdown_path),
        "status": "ready",
    }


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_document(document_id: uuid.UUID) -> None:
    deleted = delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Knowledge-base document not found.")
