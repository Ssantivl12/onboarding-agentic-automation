# 30X Onboarding Agent - Backend

Agente de onboarding para 30X. Responde preguntas sobre los 3 documentos internos con fidelidad al corpus: responde solo lo que esta en los docs, se abstiene cuando algo no esta y escala al humano correcto.

## Como correr

```bash
# 1. Instalar dependencias
uv sync

# 2. Configurar credenciales y Postgres
cp .env.example .env
# Editar .env, elegir el proveedor LLM y setear DATABASE_URL

# 3. Levantar el servidor
uv run uvicorn app.main:app --reload
```

El servidor queda en `http://localhost:8000`.

## Proveedores LLM

El backend es agnostico al proveedor desde la capa de orquestacion: `OnboardingAgent` depende de la interfaz `LLMProvider`, y `LLM_PROVIDER` decide que implementacion se usa al arrancar.

Opciones soportadas:

| `LLM_PROVIDER` | API | Key |
|---|---|---|
| `openai` | OpenAI Responses API | `OPENAI_API_KEY` o `LLM_API_KEY` |
| `claude` / `anthropic` | Anthropic Messages API | `ANTHROPIC_API_KEY` o `LLM_API_KEY` |
| `openai-compatible` | Endpoint compatible con `/v1/chat/completions` | `LLM_API_KEY` |
| `fake` | Testing local sin API real | No requiere key |

Ejemplo con OpenAI:

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.4-nano
OPENAI_API_KEY=sk-...
```

Ejemplo con Anthropic:

```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=sk-ant-...
```

Ejemplo con un proveedor OpenAI-compatible:

```bash
LLM_PROVIDER=openai-compatible
LLM_MODEL=provider-model-name
LLM_API_KEY=...
LLM_BASE_URL=https://api.provider.com/v1
```

Para agregar otro proveedor, crear una clase que implemente:

```python
class LLMProvider(Protocol):
    def generate(self, system: str, messages: list[Message]) -> str: ...
```

y registrarla en `src/app/llm/factory.py`.

## Probar sin API key

Para verificar el endpoint sin llamar a una API real, configura `LLM_PROVIDER=fake` en `.env`:

```bash
LLM_PROVIDER=fake
LLM_MODEL=fake
LLM_API_KEY=
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/onboarding_agent
```

```bash
# Verificar health
curl http://localhost:8000/health
# {"ok": true}

# Probar chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Que es 30X?", "session_id": "test-1"}'
```

La respuesta del `FakeProvider` incluye un eco de la pregunta y una cita fija del Doc1. Puedes hacer multiples requests con el mismo `session_id` para verificar que el historial persiste entre turnos.

## Knowledge Base por UI

El backend permite cargar documentos desde la interfaz grafica. Cada upload:

1. Guarda el archivo original en `KB_UPLOAD_DIR`.
2. Convierte el contenido a Markdown.
3. Guarda el Markdown en `KB_DIR`, que es lo que el chat agrega a la ventana de contexto.
4. Registra metadata y referencias de ambos archivos en Postgres usando SQLAlchemy.

Si se elimina un documento con la API, se borra el archivo original, el Markdown generado y el registro de Postgres.

Solo se aceptan PDFs de hasta 10 MB. El conversor intenta detectar tablas y volcarlas como tablas Markdown para que el modelo preserve mejor esa estructura en contexto.

Para crear las tablas manualmente antes de levantar la API:

```bash
uv run python -c "from app.db import init_db; init_db(); print('DB migrated')"
```

## Variables de entorno

| Variable | Default | Descripcion |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai`, `claude`/`anthropic`, `openai-compatible` o `fake` |
| `LLM_MODEL` | `gpt-5.4-nano` | Modelo del proveedor elegido |
| `LLM_API_KEY` | _(vacio)_ | API key generica usada si no hay key especifica |
| `OPENAI_API_KEY` | _(vacio)_ | API key para OpenAI |
| `ANTHROPIC_API_KEY` | _(vacio)_ | API key para Anthropic |
| `LLM_BASE_URL` | _(vacio)_ | Base URL opcional para proveedores OpenAI-compatible |
| `DATABASE_URL` | _(vacio)_ | URL de Postgres para metadata de documentos KB |
| `KB_DIR` | `kb` | Directorio donde se escriben los Markdown que entran al contexto |
| `KB_UPLOAD_DIR` | `kb/_uploads` | Directorio donde se guardan los archivos originales subidos |
| `KB_MAX_UPLOAD_MB` | `10` | Tamano maximo por PDF subido |

## API

### `POST /chat`

```json
// Request
{ "message": "Como funciona el onboarding?", "session_id": "abc-123" }

// Response
{
  "reply": "Segun los documentos...",
  "source": "03_equipo_herramientas.md - Tu primera semana en 30X",
  "escalated_to": null,
  "session_id": "abc-123"
}
```

- `source`: seccion del doc de origen, parseada del tag `<source>` en la respuesta del modelo.
- `escalated_to`: rol al que escalar si aplica, parseado de `<escalated_to>`.

### `GET /health`

```json
{ "ok": true }
```

### `GET /kb/documents`

Lista documentos subidos por la UI.

```json
[
  {
    "id": "6f6fd703-53de-48fd-af7b-36fd549daef2",
    "original_filename": "manual.pdf",
    "stored_filename": "manual-6f6fd703.pdf",
    "content_type": "application/pdf",
    "size_bytes": 123456,
    "sha256": "...",
    "pdf_path": "kb/_uploads/manual-6f6fd703.pdf",
    "markdown_path": "kb/manual-6f6fd703.md",
    "status": "ready",
    "error": null
  }
]
```

### `POST /kb/documents`

Sube un archivo multipart con campo `file`.

```bash
curl -X POST http://localhost:8000/kb/documents \
  -F "file=@manual.pdf"
```

### `DELETE /kb/documents/{document_id}`

Elimina metadata, archivo original y Markdown generado. Devuelve `204 No Content`.

## FAQ de evaluacion

Checklist para correr con un proveedor real:

1. **Que es 30X?** -> Descripcion + fundadores desde `01_organizacion.md`
2. **Cuales son los programas disponibles?** -> Tabla completa desde `02_programas_operacion.md`
3. **Con quien hablo si tengo un bloqueo tecnico?** -> Chief of Staff + gap marcado
4. **Como pido acceso a una herramienta?** -> Escalado a lider de area (`03_equipo_herramientas.md`)
5. **Cual es el NPS objetivo post-programa?** -> > 60 (`02_programas_operacion.md - Metricas`)
