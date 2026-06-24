# Backend Docs

Documentacion tecnica del backend full-context.

## Indice

- [Arquitectura](architecture.md)
- [Configuracion y entorno](configuration.md)
- [Flujo full-context](full-context-flow.md)
- [Knowledge base](knowledge-base.md)
- [API](api.md)
- [Diagramas Mermaid](diagrams.md)
- [Guia de desarrollo](development.md)

## Vista rapida

El backend esta organizado por responsabilidad:

```text
src/app/
|-- api/    # Routers FastAPI
|-- core/   # Orquestacion conversacional y prompts
|-- kb/     # Gestion de PDFs, Markdown y carga de contexto
|-- llm/    # Abstraccion de proveedores LLM
|-- config.py
|-- db.py
`-- main.py
```

La ruta critica del producto es:

1. `POST /kb/documents` guarda PDFs y genera Markdown.
2. `POST /chat` carga todos los Markdown disponibles.
3. El LLM recibe system prompt + knowledge base completa + historial.
4. El backend limpia tags de metadata y devuelve la respuesta al frontend.
