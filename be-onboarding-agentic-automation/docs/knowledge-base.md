# Knowledge Base

## Entrada

La UI usa:

```http
POST /kb/documents
Content-Type: multipart/form-data
```

El campo debe llamarse `file`.

## Validaciones

El backend acepta:

- Solo PDFs.
- Archivos no vacios.
- Tamano maximo definido por `KB_MAX_UPLOAD_MB`.

## Flujo de subida

1. `api/kb.py` valida tipo y contenido.
2. `kb/documents.py` genera un UUID.
3. El nombre del archivo se normaliza.
4. El PDF se guarda en `KB_UPLOAD_DIR`.
5. `kb/converter.py` convierte el PDF a Markdown.
6. El Markdown se guarda en `KB_DIR`.
7. Se registra metadata en `kb_documents`.

Si algo falla despues de escribir archivos, se eliminan los archivos parciales.

## Conversion PDF a Markdown

`converter.py` usa PyMuPDF.

- Extrae texto por pagina.
- Intenta detectar tablas con `page.find_tables()`.
- Convierte tablas detectadas a Markdown.
- Si no hay texto extraible, escribe una nota de documento sin texto.

## Carga en chat

`kb/loader.py` lee archivos `*.md` dentro de `KB_DIR`.

No carga:

- Archivos que no sean Markdown.
- Archivos Markdown cuyo nombre empieza con `_`.

El loader cachea contenido por `mtime` para evitar leer todo desde disco en cada request si nada cambio.

## Borrado

`DELETE /kb/documents/{document_id}`:

1. Busca metadata en Postgres.
2. Borra la fila.
3. Borra el PDF original.
4. Borra el Markdown generado.
5. Limpia el cache del Markdown.
