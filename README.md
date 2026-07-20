# Onboarding Agent

Monorepo para un prototipo de agente de onboarding con frontend web y backend FastAPI. La aplicacion permite cargar PDFs de la knowledge base, indexarlos con un flujo RAG y conversar con un asistente que responde usando solo la informacion recuperada de esos documentos.

## Estructura

```text
.
|-- be-onboarding-agentic-automation/  # API FastAPI, ingesta de PDFs, RAG y LLM
`-- fe-onboarding-agentic-automation/  # UI React/Vite para chat y knowledge base
```

## Que hace el proyecto

- El frontend muestra un chat tipo LLM y una vista de Knowledge Base.
- La UI permite subir, listar y borrar PDFs.
- El backend convierte los PDFs a Markdown, los divide en chunks, genera embeddings y guarda todo en Postgres + pgvector.
- El chat usa retrieval hibrido, valida si la pregunta es respondible con los documentos y genera una respuesta con fuentes.

## Requisitos

- Python 3.12+
- `uv`
- Node.js 20+
- npm
- Postgres con la extension `pgvector`
- Una API key para el proveedor LLM y embeddings. Para el flujo RAG actual, embeddings usa OpenAI.

## Como correr el proyecto

### 1. Levantar backend

```powershell
cd be-onboarding-agentic-automation
uv sync
Copy-Item .env.example .env
```

Edita `.env` con `DATABASE_URL`, `OPENAI_API_KEY` o `LLM_API_KEY`, y el proveedor/modelo que quieras usar.

```powershell
uv run uvicorn app.main:app --reload
```

El backend queda en `http://localhost:8000`.

### 2. Levantar frontend

En otra terminal:

```powershell
cd fe-onboarding-agentic-automation
npm install
npm run dev
```

El frontend queda normalmente en `http://localhost:5173`.

En desarrollo, Vite proxya `/chat`, `/health` y `/kb` hacia `http://localhost:8000`, asi que no necesitas configurar `VITE_API_URL` si corres ambos servicios localmente.

## Documentacion por paquete

- Backend setup: [be-onboarding-agentic-automation/README.md](be-onboarding-agentic-automation/README.md)
- Frontend setup: [fe-onboarding-agentic-automation/README.md](fe-onboarding-agentic-automation/README.md)
- Backend docs tecnicos: [be-onboarding-agentic-automation/docs/README.md](be-onboarding-agentic-automation/docs/README.md)

## Flujo basico de uso

1. Corre backend y frontend.
2. Abre la UI.
3. Entra a `Knowledge base`.
4. Sube PDFs de onboarding.
5. Vuelve al chat y pregunta sobre el contenido cargado.

Si no hay documentos indexados, el backend se abstiene porque no tiene contexto recuperable.
