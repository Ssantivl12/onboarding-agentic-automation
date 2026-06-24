# 30X Onboarding Agent - Frontend

Frontend React/Vite para el prototipo de onboarding. Incluye una UI de chat tipo LLM y una vista de Knowledge Base para subir, listar y borrar PDFs.

## Requisitos

- Node.js 20+
- npm
- Backend corriendo en `http://localhost:8000`

## Instalacion

```powershell
npm install
```

## Ejecutar en desarrollo

```powershell
npm run dev
```

Vite levanta normalmente en `http://localhost:5173`.

El archivo `vite.config.js` proxya estas rutas al backend local:

- `/chat`
- `/health`
- `/kb`

Por eso, si backend y frontend corren localmente, no hace falta configurar variables extra.

## Configurar API externa

Si quieres apuntar el frontend a otro backend, define `VITE_API_URL` antes de ejecutar Vite:

```powershell
$env:VITE_API_URL="http://localhost:8000"
npm run dev
```

## Scripts

```powershell
npm run dev        # servidor Vite
npm run typecheck  # TypeScript sin emitir build
npm run build      # build de produccion
npm run preview    # preview del build
```

## Flujo de uso

1. Corre el backend.
2. Corre el frontend.
3. Abre la UI.
4. Entra a `Knowledge base` y sube PDFs.
5. Vuelve a `Chat` y pregunta sobre los documentos cargados.

## Contrato con backend

El frontend consume:

- `POST /chat`
- `GET /kb/documents`
- `POST /kb/documents`
- `DELETE /kb/documents/{document_id}`

El endpoint `/rag/search` existe solo para debugging tecnico desde backend/API y no es usado por la UI.
