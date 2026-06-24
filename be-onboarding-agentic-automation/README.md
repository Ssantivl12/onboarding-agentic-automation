# 30X Onboarding Agent - Backend

Backend FastAPI para el agente de onboarding. Implementa la API de chat, la gestion de documentos de knowledge base y el pipeline RAG completo sobre Postgres + pgvector.

## Requisitos

- Python 3.12+
- `uv`
- Postgres con extension `pgvector`
- API key para el proveedor LLM
- API key de OpenAI o `LLM_API_KEY` para embeddings

## Instalacion

```powershell
uv sync
Copy-Item .env.example .env
```

Edita `.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/onboarding_agent
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.4-nano
OPENAI_API_KEY=sk-...
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

La aplicacion intenta ejecutar `CREATE EXTENSION IF NOT EXISTS vector` al arrancar. Si Postgres no tiene pgvector disponible, el backend falla de forma explicita.

## Ejecutar

```powershell
uv run uvicorn app.main:app --reload
```

Servidor local: `http://localhost:8000`

Documentacion OpenAPI: `http://localhost:8000/docs`

Healthcheck:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

## Verificacion rapida

```powershell
uv run python -m compileall src
```

Subir un PDF:

```powershell
curl.exe -X POST http://localhost:8000/kb/documents -F "file=@30X_Doc1_Organizacion.pdf"
```

Buscar chunks recuperados:

```powershell
curl.exe -X POST http://localhost:8000/rag/search -H "Content-Type: application/json" -d "{\"query\":\"Make automatizaciones\",\"top_k\":5}"
```

Preguntar al chat:

```powershell
curl.exe -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"message\":\"Que herramientas usan para automatizaciones?\",\"session_id\":\"demo\"}"
```

## Variables principales

| Variable | Default | Uso |
|---|---|---|
| `DATABASE_URL` | vacio | Conexion SQLAlchemy a Postgres con pgvector. Requerida. |
| `LLM_PROVIDER` | `openai` | Proveedor generativo: `openai`, `claude`, `anthropic`, `openai-compatible` o `fake`. |
| `LLM_MODEL` | `gpt-5.4-nano` | Modelo para chat, answerability y query rewrite. |
| `LLM_API_KEY` | vacio | API key generica de fallback. |
| `OPENAI_API_KEY` | vacio | Key de OpenAI para LLM y embeddings. |
| `ANTHROPIC_API_KEY` | vacio | Key de Anthropic si usas Claude. |
| `LLM_BASE_URL` | vacio | Base URL para proveedores OpenAI-compatible. |
| `EMBEDDING_PROVIDER` | `openai` | Proveedor de embeddings. En este prototipo solo `openai`. |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Modelo de embeddings. |
| `EMBEDDING_DIMENSIONS` | `1536` | Dimension del vector en pgvector. |
| `RAG_TOP_K` | `5` | Chunks enviados al modelo. |
| `RAG_CANDIDATES` | `20` | Candidatos recuperados antes de fusionar ranking. |
| `RAG_MIN_VECTOR_SCORE` | `0.2` | Score vectorial minimo aceptado. |
| `RAG_ENABLE_ANSWERABILITY` | `true` | Activa la compuerta de answerability. |
| `KB_DIR` | `kb` | Carpeta donde se guardan Markdown generados. |
| `KB_UPLOAD_DIR` | `kb/_uploads` | Carpeta donde se guardan PDFs subidos. |
| `KB_MAX_UPLOAD_MB` | `10` | Tamano maximo por PDF. |

## Mas documentacion

- Indice tecnico: [docs/README.md](docs/README.md)
- Arquitectura: [docs/architecture.md](docs/architecture.md)
- Pipeline de ingesta: [docs/ingestion.md](docs/ingestion.md)
- Flujo de chat RAG: [docs/chat-rag-flow.md](docs/chat-rag-flow.md)
- API: [docs/api.md](docs/api.md)
- Diagramas Mermaid: [docs/diagrams.md](docs/diagrams.md)
