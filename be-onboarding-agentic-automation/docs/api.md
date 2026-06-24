# API

Base URL local:

```text
http://localhost:8000
```

## `GET /health`

Verifica que el backend responde.

Respuesta:

```json
{
  "status": "ok"
}
```

## `POST /chat`

Endpoint usado por la UI de chat.

Request:

```json
{
  "message": "Que es 30X?",
  "session_id": "demo"
}
```

Response:

```json
{
  "reply": "Respuesta del asistente",
  "source": "archivo.pdf - seccion",
  "escalated_to": null,
  "session_id": "demo"
}
```

## `GET /kb/documents`

Lista documentos subidos.

Response:

```json
[
  {
    "id": "uuid",
    "original_filename": "30X_Doc1_Organizacion.pdf",
    "stored_filename": "30X_Doc1_Organizacion-abcd1234.pdf",
    "content_type": "application/pdf",
    "size_bytes": 12345,
    "sha256": "...",
    "pdf_path": "kb/_uploads/...",
    "markdown_path": "kb/...",
    "status": "ready",
    "error": null,
    "created_at": "2026-06-24T00:00:00Z",
    "updated_at": "2026-06-24T00:00:00Z"
  }
]
```

## `POST /kb/documents`

Sube e indexa un PDF de forma sincronica.

```powershell
curl.exe -X POST http://localhost:8000/kb/documents -F "file=@documento.pdf"
```

Errores esperados:

- `400`: archivo vacio, PDF demasiado grande o sin chunks indexables.
- `415`: archivo no PDF.
- `500`: error inesperado de conversion, embeddings o base.

## `DELETE /kb/documents/{document_id}`

Borra documento, chunks, PDF y Markdown.

Respuesta exitosa:

```http
204 No Content
```

Si no existe:

```http
404 Not Found
```

## `POST /rag/search`

Endpoint de debugging. No lo usa el frontend.

Request:

```json
{
  "query": "Make automatizaciones",
  "top_k": 5
}
```

Response:

```json
[
  {
    "chunk_id": "uuid",
    "document_id": "uuid",
    "document_name": "30X_Doc3_Equipo_Herramientas.pdf",
    "section_title": "Page 2",
    "content": "Texto del chunk",
    "vector_score": 0.81,
    "lexical_score": 0.19,
    "score": 0.032
  }
]
```

Usalo para validar que la pregunta recupera chunks correctos antes de probar `/chat`.
