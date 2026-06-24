# Configuracion y Entorno

## Archivo `.env`

Copia `.env.example`:

```powershell
Copy-Item .env.example .env
```

Variables minimas:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/onboarding_agent
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.4-nano
OPENAI_API_KEY=sk-...
```

## Base de datos

`DATABASE_URL` apunta a Postgres y se usa para guardar metadata de documentos.

Si `DATABASE_URL` no esta configurado:

- El backend puede arrancar.
- Los endpoints de knowledge base fallan con `503` cuando intentan usar DB.
- El chat puede seguir leyendo Markdown existentes en `KB_DIR`.

## Proveedor LLM

`LLM_PROVIDER` soporta:

- `openai`
- `claude`
- `anthropic`
- `openai-compatible`
- `fake`

Resolucion de API keys:

- OpenAI: `OPENAI_API_KEY` o `LLM_API_KEY`.
- Anthropic: `ANTHROPIC_API_KEY` o `LLM_API_KEY`.
- OpenAI-compatible: `LLM_API_KEY` y opcionalmente `LLM_BASE_URL`.
- Fake: no requiere key.

## Archivos locales

| Variable | Uso |
|---|---|
| `KB_UPLOAD_DIR` | Carpeta de PDFs subidos. |
| `KB_DIR` | Carpeta de Markdown generado. |
| `KB_MAX_UPLOAD_MB` | Limite por archivo PDF. |

El chat carga archivos `*.md` dentro de `KB_DIR`, excepto nombres que empiezan con `_`.

## Probar con proveedor fake

```env
LLM_PROVIDER=fake
LLM_MODEL=fake
LLM_API_KEY=
```

Esto permite validar backend/frontend sin gastar tokens ni depender de una API externa.
