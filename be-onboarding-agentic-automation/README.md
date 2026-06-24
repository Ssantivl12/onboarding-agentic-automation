# 30X Onboarding Agent - Backend

Agente de onboarding para 30X. Responde preguntas sobre los 3 documentos internos con fidelidad al corpus: responde solo lo que esta en los docs, se abstiene cuando algo no esta y escala al humano correcto.

## Como correr

```bash
# 1. Instalar dependencias
uv sync

# 2. Configurar credenciales
cp .env.example .env
# Editar .env y elegir el proveedor LLM

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

## Como actualizar la Knowledge Base

La KB vive en `kb/*.md`. Para actualizar:

1. Editar o reemplazar el `.md` correspondiente en `kb/`.
2. No hace falta reiniciar: el loader detecta el cambio de `mtime` y recarga en la proxima query.

Los PDFs originales estan archivados en `kb/_archive/`.

## Variables de entorno

| Variable | Default | Descripcion |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai`, `claude`/`anthropic`, `openai-compatible` o `fake` |
| `LLM_MODEL` | `gpt-5.4-nano` | Modelo del proveedor elegido |
| `LLM_API_KEY` | _(vacio)_ | API key generica usada si no hay key especifica |
| `OPENAI_API_KEY` | _(vacio)_ | API key para OpenAI |
| `ANTHROPIC_API_KEY` | _(vacio)_ | API key para Anthropic |
| `LLM_BASE_URL` | _(vacio)_ | Base URL opcional para proveedores OpenAI-compatible |

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

## FAQ de evaluacion

Checklist para correr con un proveedor real:

1. **Que es 30X?** -> Descripcion + fundadores desde `01_organizacion.md`
2. **Cuales son los programas disponibles?** -> Tabla completa desde `02_programas_operacion.md`
3. **Con quien hablo si tengo un bloqueo tecnico?** -> Chief of Staff + gap marcado
4. **Como pido acceso a una herramienta?** -> Escalado a lider de area (`03_equipo_herramientas.md`)
5. **Cual es el NPS objetivo post-programa?** -> > 60 (`02_programas_operacion.md - Metricas`)
