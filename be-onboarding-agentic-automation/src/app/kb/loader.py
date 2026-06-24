import os
from app.config import settings

# {filepath: (mtime, content)}
_cache: dict[str, tuple[float, str]] = {}


def load_kb() -> str:
    kb_dir = settings.kb_dir
    files = sorted(
        p for p in kb_dir.glob("*.md") if not p.name.startswith("_")
    )
    parts: list[str] = []
    for path in files:
        mtime = os.path.getmtime(path)
        cached_mtime, cached_content = _cache.get(str(path), (0.0, ""))
        if mtime != cached_mtime:
            content = path.read_text(encoding="utf-8")
            _cache[str(path)] = (mtime, content)
        else:
            content = cached_content
        parts.append(f"### [{path.name}]\n\n{content}")
    return "\n\n---\n\n".join(parts)
