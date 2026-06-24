# 30X Onboarding Agent - Backend RAG

Backend FastAPI para un agente de onboarding 100% RAG. Los PDFs se suben por API/UI, se convierten a Markdown, se dividen en chunks estructurales, se indexan con embeddings OpenAI en Postgres + pgvector y el chat responde solo desde los chunks recuperados.

## Como correr

```bash
uv sync
cp .env.example .env
```

Configura `.env`:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/onboarding_agent
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.4-nano
OPENAI_API_KEY=sk-...
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

La base debe ser Postgres con pgvector disponible. El backend intenta crear `CREATE EXTENSION IF NOT EXISTS vector` al arrancar y falla de forma explicita si no puede.

```bash
uv run uvicorn app.main:app --reload
```

El servidor queda en `http://localhost:8000`.

## Flujo RAG

1. `POST /kb/documents` recibe un PDF.
2. El PDF se guarda en `KB_UPLOAD_DIR`.
3. Se convierte a Markdown con PyMuPDF, preservando tablas detectables como Markdown.
4. El Markdown se divide por estructura de headings y bloques de tabla.
5. Cada chunk se embebe con OpenAI embeddings.
6. Documento, chunks y embeddings quedan persistidos en Postgres.
7. `POST /chat` reformula la consulta con historial, recupera chunks por busqueda hibrida, valida answerability y genera una respuesta usando solo el contexto recuperado.

## Variables principales

| Variable | Default | Descripcion |
|---|---|---|
| `DATABASE_URL` | _(vacio)_ | Postgres con pgvector. Requerido. |
| `LLM_PROVIDER` | `openai` | `openai`, `claude`/`anthropic`, `openai-compatible` o `fake`. |
| `LLM_MODEL` | `gpt-5.4-nano` | Modelo generativo para chat, answerability y query rewrite. |
| `OPENAI_API_KEY` | _(vacio)_ | API key para OpenAI y embeddings. |
| `LLM_API_KEY` | _(vacio)_ | Key generica de fallback. |
| `EMBEDDING_PROVIDER` | `openai` | Solo `openai` en este prototipo. |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Modelo de embeddings. |
| `EMBEDDING_DIMENSIONS` | `1536` | Dimension del vector persistido. |
| `RAG_TOP_K` | `5` | Chunks finales enviados al modelo. |
| `RAG_CANDIDATES` | `20` | Candidatos por retriever antes de fusionar. |
| `RAG_MIN_VECTOR_SCORE` | `0.2` | Filtro minimo para resultados vectoriales. |
| `RAG_ENABLE_ANSWERABILITY` | `true` | Activa compuerta LLM antes de generar. |

## API

### `POST /kb/documents`

Sube un PDF, lo convierte e indexa de forma sincronica.

```bash
curl -X POST http://localhost:8000/kb/documents \
  -F "file=@30X_Doc1_Organizacion.pdf"
```

### `GET /kb/documents`

Lista PDFs cargados.

### `DELETE /kb/documents/{document_id}`

Elimina metadata, chunks, PDF y Markdown.

### `POST /rag/search`

Endpoint de debugging para inspeccionar retrieval.

```bash
curl -X POST http://localhost:8000/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Make automatizaciones", "top_k": 5}'
```

### `POST /chat`

```json
{
  "message": "Que herramientas usan para automatizaciones?",
  "session_id": "abc-123"
}
```

Respuesta:

```json
{
  "reply": "Segun los documentos...",
  "source": "30X_Doc3_Equipo_Herramientas.pdf - Stack de herramientas",
  "escalated_to": null,
  "session_id": "abc-123"
}
```

## Pruebas manuales recomendadas

1. Subir los PDFs de onboarding desde la UI o `POST /kb/documents`.
2. Probar `/rag/search` con: `Make`, `Chief of Staff`, `NPS objetivo`, `HubSpot`.
3. Probar `/chat`:
   - `Que es 30X?`
   - `Que herramientas usan para automatizaciones?`
   - `Con quien hablo si tengo un bloqueo tecnico?`
   - `Cual es la politica de vacaciones?`
4. Confirmar que preguntas fuera del corpus se abstienen y escalan sin inventar.
