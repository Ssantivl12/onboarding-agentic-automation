# 30X Onboarding Agent

Monorepo para un prototipo de agente de onboarding con frontend web y backend FastAPI. La aplicacion permite cargar PDFs de la knowledge base, convertirlos a Markdown y conversar con un asistente que usa esos documentos completos como contexto.

## Estructura

```text
.
|-- be-onboarding-agentic-automation/  # API FastAPI, LLM, DB y knowledge base
`-- fe-onboarding-agentic-automation/  # UI React/Vite para chat y gestion de PDFs
```

## Que hace el proyecto

- El frontend muestra un chat tipo LLM y una vista de Knowledge Base.
- La UI permite subir, listar y borrar PDFs.
- El backend convierte PDFs a Markdown y guarda metadata en Postgres.
- El chat carga los Markdown disponibles y los agrega al prompt como contexto completo.
- El proveedor LLM es configurable: OpenAI, Anthropic/Claude, OpenAI-compatible o fake.

## Requisitos

- Python 3.12+
- `uv`
- Node.js 20+
- npm
- Postgres para metadata de documentos subidos
- Una API key para el proveedor LLM elegido, salvo que uses `LLM_PROVIDER=fake`

## Como correr el proyecto

### 1. Levantar backend

```powershell
cd be-onboarding-agentic-automation
uv sync
Copy-Item .env.example .env
```

Edita `.env` con `DATABASE_URL` y el proveedor LLM.

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

En esta rama el enfoque es full-context: todos los Markdown cargados entran al prompt del chat.
