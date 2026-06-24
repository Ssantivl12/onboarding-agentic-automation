# Pipeline de Ingesta

## Entrada

La ingesta entra por:

```http
POST /kb/documents
Content-Type: multipart/form-data
```

El archivo debe ser PDF y no puede superar `KB_MAX_UPLOAD_MB`.

## Flujo

1. `api/kb.py` valida `content_type` y archivo no vacio.
2. `kb/documents.py` genera un UUID para el documento.
3. El nombre original se normaliza para evitar rutas peligrosas.
4. El PDF se guarda en `KB_UPLOAD_DIR`.
5. `kb/converter.py` convierte el PDF a Markdown con PyMuPDF.
6. El Markdown se guarda en `KB_DIR`.
7. `rag/chunker.py` divide el Markdown en chunks.
8. `rag/embeddings.py` genera embeddings para cada chunk.
9. `db.py` persiste metadata y chunks en una transaccion.

Si cualquier paso falla despues de escribir archivos, `create_document()` elimina el PDF y Markdown creados antes de propagar el error.

## Conversion PDF a Markdown

`converter.py` usa PyMuPDF:

- Extrae texto por pagina con `page.get_text("text")`.
- Intenta detectar tablas con `page.find_tables()`.
- Convierte tablas detectadas a Markdown.
- Si no hay texto extraible, genera un Markdown con una nota de documento vacio.

Formato aproximado:

```markdown
# archivo.pdf

## Page 1

Texto extraido...

## Page 1 Tables

### Table 1

| Columna | Valor |
| --- | --- |
| ... | ... |
```

## Chunking

`chunker.py` divide el Markdown por headings `#`, `##` y `###`.

Reglas:

- Mantiene `section_title` para cada chunk.
- Agrupa bloques hasta un objetivo aproximado de tokens.
- Mantiene tablas Markdown juntas cuando es posible.
- Si un bloque excede el maximo, lo divide por lineas.

El conteo de tokens es estimado con palabras, suficiente para controlar tamano en este prototipo.

## Persistencia

Se inserta una fila en `kb_documents` y varias filas en `kb_chunks`.

Campos importantes de chunk:

- `document_id`
- `chunk_index`
- `section_title`
- `content`
- `token_count`
- `embedding`

## Borrado

`DELETE /kb/documents/{document_id}`:

1. Busca el documento.
2. Borra la fila de `kb_documents`.
3. Los chunks se borran por cascade.
4. Borra PDF y Markdown del filesystem.
