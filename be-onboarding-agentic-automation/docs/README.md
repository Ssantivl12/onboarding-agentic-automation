# Backend Docs

Documentacion tecnica del backend RAG.

## Indice

- [Arquitectura](architecture.md)
- [Configuracion y entorno](configuration.md)
- [Pipeline de ingesta](ingestion.md)
- [Flujo de chat RAG](chat-rag-flow.md)
- [API](api.md)
- [Diagramas Mermaid](diagrams.md)
- [Guia de desarrollo](development.md)

## Vista rapida

El backend esta organizado por responsabilidad:

```text
src/app/
|-- api/    # Routers FastAPI
|-- core/   # Orquestacion conversacional y prompts
|-- kb/     # Gestion de PDFs, Markdown y documentos
|-- llm/    # Abstraccion de proveedores LLM
|-- rag/    # Chunking, embeddings y retrieval
|-- config.py
|-- db.py
`-- main.py
```

La ruta critica del producto es:

1. `POST /kb/documents` guarda e indexa PDFs.
2. `POST /chat` recupera chunks relevantes.
3. El answerability gate decide si se puede responder.
4. El LLM genera una respuesta basada solo en contexto recuperado.
