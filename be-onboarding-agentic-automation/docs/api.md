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
  "ok": true
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
  "source": "archivo.md - seccion",
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
    "original_filename": "manual.pdf",
    "stored_filename": "manual-abcd1234.pdf",
    "content_type": "application/pdf",
    "size_bytes": 12345,
    "sha256": "...",
    "pdf_path": "kb/_uploads/manual-abcd1234.pdf",
    "markdown_path": "kb/manual-abcd1234.md",
    "status": "ready",
    "error": null,
    "created_at": "2026-06-24T00:00:00Z",
    "updated_at": "2026-06-24T00:00:00Z"
  }
]
```

## `POST /kb/documents`

Sube un PDF y lo convierte a Markdown de forma sincronica.

```powershell
curl.exe -X POST http://localhost:8000/kb/documents -F "file=@manual.pdf"
```

Errores esperados:

- `400`: archivo vacio o PDF demasiado grande.
- `415`: archivo no PDF.
- `503`: `DATABASE_URL` no configurado para registrar metadata.
- `500`: error inesperado de conversion o base.

## `DELETE /kb/documents/{document_id}`

Borra metadata, PDF y Markdown.

Respuesta exitosa:

```http
204 No Content
```

Si no existe:

```http
404 Not Found
```
