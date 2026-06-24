# Arquitectura

## Objetivo

El backend implementa un agente de onboarding con enfoque full-context. El sistema no hace retrieval ni embeddings: carga todos los Markdown disponibles en `KB_DIR` y los concatena al system prompt antes de llamar al LLM.

## Capas principales

### `main.py`

Punto de entrada FastAPI.

- Crea la app.
- Configura CORS.
- Ejecuta `init_db()` en startup.
- Construye el proveedor LLM con `get_provider()`.
- Crea `OnboardingAgent`.
- Registra routers de chat y knowledge base.

### `config.py`

Centraliza configuracion desde `.env`.

- Proveedor/modelo LLM.
- Conexion a Postgres.
- Directorios para PDFs y Markdown.
- Limite de tamano de upload.

### `db.py`

Define SQLAlchemy para metadata de documentos.

- `KnowledgeBaseDocument`: una fila por PDF subido.
- `init_db()`: crea tablas si `DATABASE_URL` existe.
- `session_scope()`: transacciones con commit/rollback.

### `api/`

Routers HTTP.

- `chat.py`: contrato de chat usado por la UI.
- `kb.py`: upload, listado y borrado de documentos.

### `kb/`

Gestion de knowledge base.

- `converter.py`: PDF a Markdown con PyMuPDF.
- `documents.py`: guarda PDFs, crea Markdown y registra metadata.
- `loader.py`: carga todos los Markdown de `KB_DIR` y los cachea por mtime.

### `core/`

Logica conversacional.

- `system_prompt.py`: instrucciones base del agente.
- `orchestrator.py`: agrega knowledge base completa al prompt, llama al LLM y limpia metadata.

### `llm/`

Abstraccion de proveedor generativo.

- `base.py`: interfaz comun.
- `providers.py`: OpenAI, Anthropic, OpenAI-compatible y fake.
- `factory.py`: seleccion por `LLM_PROVIDER`.

## Persistencia

Postgres guarda metadata de documentos subidos. Los contenidos reales viven en disco:

- PDF original: `KB_UPLOAD_DIR`.
- Markdown convertido: `KB_DIR`.

El chat no lee el PDF original; lee los Markdown generados.

## Cache de knowledge base

`kb/loader.py` mantiene un cache en memoria por ruta y `mtime`.

Implicaciones:

- Si el Markdown cambia en disco, se recarga al cambiar `mtime`.
- Si se borra un documento desde la API, se limpia el cache de ese Markdown.
- Reiniciar el backend borra el cache y lo reconstruye en la siguiente request de chat.

## Estado conversacional

`OnboardingAgent` guarda historial por `session_id` en memoria del proceso.

Implicaciones:

- Reiniciar el backend borra historiales.
- Multiples workers no compartirian memoria.
- Para produccion, conviene mover sesiones a Redis o base de datos.
