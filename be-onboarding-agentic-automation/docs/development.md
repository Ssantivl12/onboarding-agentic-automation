# Guia de Desarrollo

## Comandos utiles

Instalar dependencias:

```powershell
uv sync
```

Compilar Python:

```powershell
uv run python -m compileall src
```

Ejecutar API:

```powershell
uv run uvicorn app.main:app --reload
```

## Pruebas manuales recomendadas

### Ingesta

1. Subir un PDF valido desde UI o `POST /kb/documents`.
2. Confirmar que aparece en `GET /kb/documents`.
3. Confirmar que se crea Markdown en `KB_DIR`.
4. Confirmar que existen chunks en `kb_chunks`.
5. Borrar el documento y verificar que desaparecen metadata, chunks, PDF y Markdown.

### Retrieval

Usar `/rag/search` con consultas conocidas:

- `Make`
- `Chief of Staff`
- `NPS objetivo`
- `HubSpot`

Validar que `content`, `document_name` y `section_title` correspondan a los PDFs esperados.

### Chat

Preguntas sugeridas:

- `Que es 30X?`
- `Que herramientas usan para automatizaciones?`
- `Con quien hablo si tengo un bloqueo tecnico?`
- `Cual es la politica de vacaciones?`

La ultima deberia abstenerse si esa informacion no esta en los documentos cargados.

## Riesgos conocidos del prototipo

- No hay migraciones formales; `create_all()` crea tablas para prototipo.
- El historial de sesiones vive en memoria.
- La ingesta es sincronica; PDFs grandes pueden bloquear la request.
- Embeddings solo soporta OpenAI.
- La extraccion de tablas depende de lo que PyMuPDF detecte en cada PDF.

## Cambios recomendados para produccion

- Agregar Alembic para migraciones.
- Mover sesiones a Redis o base persistente.
- Procesar ingesta en background jobs.
- Agregar autenticacion y limites por usuario.
- Registrar trazas de retrieval y costos por request.
- Agregar tests automatizados para chunking, retrieval y endpoints.
