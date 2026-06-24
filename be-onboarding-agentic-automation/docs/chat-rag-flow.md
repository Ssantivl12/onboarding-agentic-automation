# Flujo de Chat RAG

## Entrada

El frontend llama:

```http
POST /chat
Content-Type: application/json
```

Payload:

```json
{
  "message": "Que herramientas usan para automatizaciones?",
  "session_id": "demo"
}
```

## Orquestacion

`core/orchestrator.py` controla el flujo.

### 1. Historial

El agente guarda mensajes por `session_id` en memoria. Usa el historial reciente para reformular preguntas de seguimiento.

### 2. Query rewrite

Si hay historial, el LLM recibe `QUERY_REWRITE_PROMPT` para convertir la pregunta actual en una consulta independiente.

Ejemplo:

```text
Usuario previo: Que herramientas usan?
Usuario actual: Y para automatizaciones?
Query rewrite: herramientas usadas para automatizaciones
```

Si el rewrite falla, se usa el mensaje original.

### 3. Retrieval hibrido

`rag/retriever.py` ejecuta:

- Busqueda vectorial con cosine distance en pgvector.
- Busqueda lexical con full-text search de Postgres.
- Fusion de rankings con Reciprocal Rank Fusion.

El resultado final son `RAG_TOP_K` chunks.

### 4. Answerability gate

Antes de generar, el LLM recibe la pregunta y los chunks candidatos. Debe responder JSON:

```json
{
  "answerable": "complete",
  "reason": "La informacion esta cubierta por los chunks.",
  "source_ids": ["..."]
}
```

Estados soportados:

- `complete`: se puede responder.
- `partial`: se responde solo lo respaldado y se marcan huecos.
- `missing`: se abstiene y recomienda escalar.
- `ambiguous`: pide aclaracion.

Si el gate falla por error de parseo o proveedor, el sistema usa un fallback conservador: responde con los chunks recuperados.

### 5. Generacion

El prompt final incluye:

- `RAG_SYSTEM_PROMPT`
- Contexto recuperado formateado por source id.
- Estado de cobertura.
- Pregunta original.

La respuesta final debe traer metadata en tags:

```xml
<source>archivo.pdf - seccion</source>
<escalated_to>Chief of Staff</escalated_to>
```

El backend elimina esos tags del texto visible y devuelve `source` y `escalated_to` como campos JSON.

## Salida

```json
{
  "reply": "Segun los documentos...",
  "source": "30X_Doc3_Equipo_Herramientas.pdf - Page 2",
  "escalated_to": null,
  "session_id": "demo"
}
```

## Abstencion

Si no hay chunks o el gate devuelve `missing`, el backend responde sin inventar:

```json
{
  "reply": "Eso no esta en los documentos de onboarding cargados. Te conviene preguntarle al Chief of Staff.",
  "source": null,
  "escalated_to": "Chief of Staff",
  "session_id": "demo"
}
```
