import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkDraft:
    chunk_index: int
    section_title: str
    content: str
    token_count: int


def chunk_markdown(markdown: str, *, target_tokens: int = 750, max_tokens: int = 1000) -> list[ChunkDraft]:
    sections = _split_sections(markdown)
    chunks: list[ChunkDraft] = []

    for section_title, section_text in sections:
        for content in _split_section(section_text, target_tokens=target_tokens, max_tokens=max_tokens):
            chunks.append(
                ChunkDraft(
                    chunk_index=len(chunks),
                    section_title=section_title,
                    content=content,
                    token_count=estimate_tokens(content),
                )
            )

    return chunks


def estimate_tokens(text: str) -> int:
    words = re.findall(r"\S+", text)
    return max(1, int(len(words) * 1.3))


def _split_sections(markdown: str) -> list[tuple[str, str]]:
    current_title = "Documento"
    current_lines: list[str] = []
    sections: list[tuple[str, str]] = []

    for line in markdown.splitlines():
        heading = re.match(r"^(#{1,3})\s+(.+?)\s*$", line)
        if heading and current_lines:
            sections.append((current_title, "\n".join(current_lines).strip()))
            current_lines = []
        if heading:
            current_title = heading.group(2).strip()
        current_lines.append(line)

    if current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))

    return [(title, text) for title, text in sections if text]


def _split_section(section_text: str, *, target_tokens: int, max_tokens: int) -> list[str]:
    blocks = _blocks(section_text)
    chunks: list[str] = []
    current: list[str] = []

    for block in blocks:
        candidate = "\n\n".join([*current, block]).strip()
        if current and estimate_tokens(candidate) > target_tokens:
            chunks.append("\n\n".join(current).strip())
            current = [block]
        else:
            current.append(block)

        if estimate_tokens("\n\n".join(current)) > max_tokens:
            oversized = "\n\n".join(current)
            chunks.extend(_split_oversized_block(oversized, max_tokens=max_tokens))
            current = []

    if current:
        chunks.append("\n\n".join(current).strip())

    return [chunk for chunk in chunks if chunk]


def _blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    in_table = False

    for line in text.splitlines():
        is_table_line = line.strip().startswith("|")
        if line.strip() == "" and not in_table:
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue

        if current and in_table and not is_table_line:
            blocks.append("\n".join(current).strip())
            current = []

        current.append(line)
        in_table = is_table_line

    if current:
        blocks.append("\n".join(current).strip())

    return [block for block in blocks if block]


def _split_oversized_block(text: str, *, max_tokens: int) -> list[str]:
    lines = text.splitlines()
    chunks: list[str] = []
    current: list[str] = []

    for line in lines:
        candidate = "\n".join([*current, line]).strip()
        if current and estimate_tokens(candidate) > max_tokens:
            chunks.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        chunks.append("\n".join(current).strip())
    return chunks
