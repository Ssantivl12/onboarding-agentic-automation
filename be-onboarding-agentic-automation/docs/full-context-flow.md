# Flujo Full-Context

## Entrada

El frontend llama:

```http
POST /chat
Content-Type: application/json
```

Payload:

```json
{
  "message": "Que es 30X?",
  "session_id": "demo"
}
```

## Orquestacion

`core/orchestrator.py` controla el flujo.

### 1. Historial

El agente recupera el historial en memoria asociado al `session_id`.

### 2. Carga de knowledge base

`load_kb()` lee todos los Markdown dentro de `KB_DIR`.

Cada archivo se agrega con este formato:

```markdown
### [archivo.md]

contenido del documento
```

Los documentos se separan con `---`.

### 3. System prompt

El system prompt final es:

```text
SYSTEM_PROMPT + load_kb()
```

Esto significa que el modelo ve instrucciones base mas todo el corpus Markdown cargado.

### 4. Llamada al proveedor LLM

El proveedor recibe:

- `system`: prompt completo con documentos.
- `messages`: historial de sesion + mensaje actual.

### 5. Limpieza de metadata

El modelo puede devolver:

```xml
<source>archivo.md - seccion</source>
<escalated_to>Chief of Staff</escalated_to>
```

El backend extrae esos tags y los elimina del texto visible.

## Salida

```json
{
  "reply": "Respuesta del asistente",
  "source": "archivo.md - seccion",
  "escalated_to": null,
  "session_id": "demo"
}
```

## Limites del enfoque

- El costo crece con el tamano total de la knowledge base.
- Puede superar el limite de contexto si se cargan muchos PDFs.
- No hay ranking ni filtrado semantico.
- Es simple y util para prototipo con pocos documentos.
