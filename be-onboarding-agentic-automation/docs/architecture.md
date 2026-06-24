# Arquitectura

## Objetivo

El backend implementa un agente de onboarding 100% RAG. No carga todos los documentos completos en el prompt; primero indexa los PDFs y luego recupera solo los chunks relevantes por pregunta.

## Capas principales

### `main.py`

Punto de entrada FastAPI.

- Crea la app.
- Configura CORS.
- Inicializa la base en startup con `init_db()`.
- Construye el proveedor LLM, embedder, retriever y agente.
- Registra routers de chat, knowledge base y RAG debug.

### `config.py`

Centraliza configuracion desde `.env`.

- Proveedor/modelo LLM.
- Conexion a Postgres.
- Configuracion de embeddings.
- Parametros RAG.
- Directorios de archivos para PDFs y Markdown.

### `db.py`

Define modelos SQLAlchemy y manejo de sesiones.

- `KnowledgeBaseDocument`: metadata del PDF.
- `KnowledgeBaseChunk`: chunks indexados con embedding pgvector.
- `init_db()`: valida `DATABASE_URL`, crea extension `vector`, tablas e indices.
- `session_scope()`: transacciones con commit/rollback.

### `api/`

Routers HTTP.

- `chat.py`: contrato de chat usado por el frontend.
- `kb.py`: upload/list/delete de documentos.
- `rag.py`: endpoint de debug para inspeccionar retrieval.

### `kb/`

Gestion documental.

- `converter.py`: PDF a Markdown con PyMuPDF.
- `documents.py`: guarda PDFs, genera Markdown, chunking, embeddings e insercion DB.

### `rag/`

Componentes RAG.

- `chunker.py`: divide Markdown por headings y bloques.
- `embeddings.py`: cliente de embeddings OpenAI.
- `retriever.py`: busqueda vectorial + lexical + fusion RRF.

### `core/`

Logica conversacional.

- `system_prompt.py`: prompts para generacion, answerability y query rewrite.
- `orchestrator.py`: flujo completo de chat RAG.

### `llm/`

Abstraccion de proveedor generativo.

- `base.py`: interfaz comun.
- `providers.py`: implementaciones OpenAI, Anthropic, OpenAI-compatible y fake.
- `factory.py`: seleccion por `LLM_PROVIDER`.

## Persistencia

La base usa Postgres con pgvector.

Tablas principales:

- `kb_documents`: una fila por PDF subido.
- `kb_chunks`: una fila por chunk indexado.

Relacion:

- Un documento tiene muchos chunks.
- Al borrar un documento, se borran sus chunks por cascade.

Indices relevantes:

- Full-text search sobre `section_title + content`.
- HNSW cosine index sobre `embedding`.

## Estado conversacional

`OnboardingAgent` guarda historial por `session_id` en memoria del proceso. Esto es suficiente para el prototipo, pero no es persistente ni distribuido.

Implicaciones:

- Reiniciar el backend borra historiales.
- Multiples workers no compartirian memoria.
- Para produccion, conviene mover sesiones a Redis o base de datos.
