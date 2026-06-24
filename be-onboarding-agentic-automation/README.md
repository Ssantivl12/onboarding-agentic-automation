# 30X Onboarding Agent - Backend

Backend FastAPI para el agente de onboarding. Esta rama implementa el flujo full-context: los PDFs subidos se convierten a Markdown, se guardan en disco y el chat carga todos los Markdown disponibles dentro del prompt del modelo.

## Requisitos

- Python 3.12+
- `uv`
- Postgres para metadata de documentos
- API key del proveedor LLM, salvo que uses `LLM_PROVIDER=fake`

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
```

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

## Probar sin API key

Configura `.env` asi:

```env
LLM_PROVIDER=fake
LLM_MODEL=fake
LLM_API_KEY=
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/onboarding_agent
```

Luego:

```powershell
uv run uvicorn app.main:app --reload
```

```powershell
curl.exe -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"message\":\"Que es 30X?\",\"session_id\":\"demo\"}"
```

## Verificacion rapida

```powershell
uv run python -m compileall src
```

Crear tablas manualmente:

```powershell
uv run python -c "from app.db import init_db; init_db(); print('DB migrated')"
```

Subir un PDF:

```powershell
curl.exe -X POST http://localhost:8000/kb/documents -F "file=@manual.pdf"
```

Preguntar al chat:

```powershell
curl.exe -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"message\":\"Como funciona el onboarding?\",\"session_id\":\"demo\"}"
```

## Variables principales

| Variable | Default | Uso |
|---|---|---|
| `LLM_PROVIDER` | `openai` | Proveedor generativo: `openai`, `claude`, `anthropic`, `openai-compatible` o `fake`. |
| `LLM_MODEL` | `gpt-5.4-nano` | Modelo del proveedor elegido. |
| `LLM_API_KEY` | vacio | API key generica de fallback. |
| `OPENAI_API_KEY` | vacio | Key de OpenAI. |
| `ANTHROPIC_API_KEY` | vacio | Key de Anthropic. |
| `LLM_BASE_URL` | vacio | Base URL para proveedores OpenAI-compatible. |
| `DATABASE_URL` | vacio | Conexion SQLAlchemy a Postgres para metadata KB. |
| `KB_DIR` | `kb` | Carpeta donde se guardan Markdown generados. |
| `KB_UPLOAD_DIR` | `kb/_uploads` | Carpeta donde se guardan PDFs subidos. |
| `KB_MAX_UPLOAD_MB` | `10` | Tamano maximo por PDF. |

## Proveedores LLM

El backend es agnostico al proveedor desde la capa de orquestacion. `OnboardingAgent` depende de la interfaz `LLMProvider`, y `LLM_PROVIDER` decide la implementacion al arrancar.

| `LLM_PROVIDER` | API | Key |
|---|---|---|
| `openai` | OpenAI Responses API | `OPENAI_API_KEY` o `LLM_API_KEY` |
| `claude` / `anthropic` | Anthropic Messages API | `ANTHROPIC_API_KEY` o `LLM_API_KEY` |
| `openai-compatible` | `/v1/chat/completions` | `LLM_API_KEY` |
| `fake` | Testing local | No requiere key |

## Mas documentacion

- Indice tecnico: [docs/README.md](docs/README.md)
- Arquitectura: [docs/architecture.md](docs/architecture.md)
- Flujo full-context: [docs/full-context-flow.md](docs/full-context-flow.md)
- Knowledge base: [docs/knowledge-base.md](docs/knowledge-base.md)
- API: [docs/api.md](docs/api.md)
- Diagramas Mermaid: [docs/diagrams.md](docs/diagrams.md)
