graph TD
    User[Usuario] --> UI[Frontend React/Vite]

    UI -->|Sube PDF| Upload[POST /kb/documents]
    Upload --> Validate[Validar PDF y tamano]
    Validate --> StorePDF[Guardar PDF en KB_UPLOAD_DIR]
    StorePDF --> Convert[Convertir PDF a Markdown]
    Convert --> StoreMD[Guardar Markdown en KB_DIR]
    StoreMD --> Chunk[Dividir Markdown en chunks]
    Chunk --> Embed[Generar embeddings OpenAI]
    Embed --> Persist[(Postgres + pgvector)]
    Persist --> ListDocs[GET /kb/documents]
    ListDocs --> UI

    UI -->|Borra documento| Delete[DELETE /kb/documents/id]
    Delete --> DeleteDB[Borrar metadata y chunks]
    DeleteDB --> DeleteFiles[Borrar PDF y Markdown]
    DeleteFiles --> UI

    UI -->|Pregunta| Chat[POST /chat]
    Chat --> Agent[OnboardingAgent]
    Agent --> History[Historial por session_id]
    History --> Rewrite{Hay historial?}
    Rewrite -->|Si| QueryRewrite[Reformular pregunta con LLM]
    Rewrite -->|No| Query[Usar pregunta original]
    QueryRewrite --> Retrieval[Retrieval hibrido]
    Query --> Retrieval

    Retrieval --> VectorSearch[Busqueda vectorial pgvector]
    Retrieval --> LexicalSearch[Busqueda lexical Postgres FTS]
    VectorSearch --> Fusion[Reciprocal Rank Fusion]
    LexicalSearch --> Fusion
    Fusion --> Chunks[Top chunks recuperados]

    Chunks --> HasChunks{Hay contexto?}
    HasChunks -->|No| Abstain[Abstenerse y escalar]
    HasChunks -->|Si| Gate[Answerability gate con LLM]

    Gate --> Decision{Resultado}
    Decision -->|missing| Abstain
    Decision -->|ambiguous| Clarify[Pedir aclaracion]
    Decision -->|partial/complete| Generate[Generar respuesta con contexto]

    Generate --> Tags[Extraer source y escalated_to]
    Tags --> Response[ChatResponse]
    Abstain --> Response
    Clarify --> Response
    Response --> UI

    UI -->|Debug tecnico| RagSearch[POST /rag/search]
    RagSearch --> Retrieval
