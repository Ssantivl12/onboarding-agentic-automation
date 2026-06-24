graph TD
    User[Usuario] --> UI[Frontend React/Vite]

    UI -->|Sube PDF| Upload[POST /kb/documents]
    Upload --> Validate[Validar PDF y tamano]
    Validate --> StorePDF[Guardar PDF en KB_UPLOAD_DIR]
    StorePDF --> Convert[Convertir PDF a Markdown]
    Convert --> StoreMD[Guardar Markdown en KB_DIR]
    StoreMD --> SaveMeta[(Postgres kb_documents)]
    SaveMeta --> ListDocs[GET /kb/documents]
    ListDocs --> UI

    UI -->|Borra documento| Delete[DELETE /kb/documents/id]
    Delete --> DeleteMeta[Borrar metadata]
    DeleteMeta --> DeleteFiles[Borrar PDF y Markdown]
    DeleteFiles --> ClearCache[Limpiar cache de Markdown]
    ClearCache --> UI

    UI -->|Pregunta| Chat[POST /chat]
    Chat --> Agent[OnboardingAgent]
    Agent --> History[Historial por session_id]
    History --> LoadKB[load_kb]
    LoadKB --> ReadMD[Leer Markdown de KB_DIR]
    ReadMD --> Cache{Cambio mtime?}
    Cache -->|Si| Reload[Recargar archivo]
    Cache -->|No| Cached[Usar cache]
    Reload --> FullContext[System prompt + knowledge base completa]
    Cached --> FullContext
    FullContext --> LLM[Proveedor LLM]
    LLM --> Tags[Extraer source y escalated_to]
    Tags --> Response[ChatResponse]
    Response --> UI
