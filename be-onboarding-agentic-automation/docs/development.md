# Guia de Desarrollo

## Comandos utiles

Instalar dependencias:

```powershell
uv sync
```

Compilar Python:

```powershell
uv run python -m compileall src
```

Ejecutar API:

```powershell
uv run uvicorn app.main:app --reload
```

Crear tablas manualmente:

```powershell
uv run python -c "from app.db import init_db; init_db(); print('DB migrated')"
```

## Pruebas manuales recomendadas

### Knowledge base

1. Subir un PDF valido desde UI o `POST /kb/documents`.
2. Confirmar que aparece en `GET /kb/documents`.
3. Confirmar que se crea Markdown en `KB_DIR`.
4. Borrar el documento y verificar que desaparecen metadata, PDF y Markdown.

### Chat

Preguntas sugeridas:

- `Que es 30X?`
- `Cuales son los programas disponibles?`
- `Con quien hablo si tengo un bloqueo tecnico?`
- `Como pido acceso a una herramienta?`
- `Cual es el NPS objetivo post-programa?`

## Riesgos conocidos del prototipo

- No hay migraciones formales; `create_all()` crea tablas para prototipo.
- El historial de sesiones vive en memoria.
- El prompt crece con todos los Markdown cargados.
- La ingesta es sincronica.
- La extraccion de tablas depende de lo que PyMuPDF detecte.

## Cambios recomendados para produccion

- Agregar Alembic para migraciones.
- Mover sesiones a Redis o base persistente.
- Procesar ingesta en background jobs.
- Agregar autenticacion y limites por usuario.
- Reemplazar full-context por RAG si el corpus crece.
- Agregar tests automatizados para conversion, loader, endpoints y proveedores.
