# Configuracion y Entorno

## Archivo `.env`

Copia `.env.example`:

```powershell
Copy-Item .env.example .env
```

Variables minimas para el flujo real:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/onboarding_agent
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.4-nano
OPENAI_API_KEY=sk-...
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

## Base de datos

`DATABASE_URL` debe apuntar a Postgres con pgvector instalado. Al arrancar, el backend ejecuta:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Si la extension no existe o el usuario no tiene permisos, la app falla con un error claro.

## Proveedor LLM

`LLM_PROVIDER` soporta:

- `openai`
- `claude`
- `anthropic`
- `openai-compatible`
- `fake`

El proveedor generativo se usa para:

- Reformular consultas con historial.
- Evaluar answerability.
- Generar la respuesta final.

## Embeddings

En este prototipo, `EMBEDDING_PROVIDER` soporta `openai`.

La API key se resuelve asi:

1. `OPENAI_API_KEY`
2. `LLM_API_KEY`

`EMBEDDING_DIMENSIONS` debe coincidir con la dimension usada por el modelo y con la columna `Vector(...)` de pgvector. Si cambias dimensiones en una base existente, recrea la tabla o aplica una migracion.

## Parametros RAG

| Variable | Uso |
|---|---|
| `RAG_TOP_K` | Cantidad final de chunks enviados al modelo. |
| `RAG_CANDIDATES` | Cantidad de candidatos por modalidad antes de fusionar. |
| `RAG_MIN_VECTOR_SCORE` | Filtro minimo para resultados vectoriales. |
| `RAG_ENABLE_ANSWERABILITY` | Activa o desactiva la compuerta de respuesta. |

## Archivos locales

| Variable | Uso |
|---|---|
| `KB_UPLOAD_DIR` | Carpeta de PDFs subidos. |
| `KB_DIR` | Carpeta de Markdown generado. |
| `KB_MAX_UPLOAD_MB` | Limite por archivo PDF. |

La base mantiene las rutas de PDF y Markdown. Al borrar un documento, el backend borra metadata, chunks y archivos locales.
