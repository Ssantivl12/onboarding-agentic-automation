from pathlib import Path


class UnsupportedKnowledgeBaseFile(ValueError):
    pass


def convert_to_markdown(source_path: Path, original_filename: str, content_type: str) -> str:
    suffix = source_path.suffix.lower()
    normalized_type = content_type.lower()

    if suffix == ".pdf" or normalized_type == "application/pdf":
        return _pdf_to_markdown(source_path, original_filename)

    raise UnsupportedKnowledgeBaseFile("Only PDF files are supported.")


def _pdf_to_markdown(source_path: Path, original_filename: str) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("pymupdf is required to convert PDFs to Markdown.") from exc

    sections: list[str] = [f"# {original_filename}"]
    with fitz.open(source_path) as doc:
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            tables = _extract_tables(page)
            if text:
                sections.append(f"## Page {page_number}\n\n{text}")
            if tables:
                sections.append(
                    f"## Page {page_number} Tables\n\n" + "\n\n".join(tables)
                )

    if len(sections) == 1:
        sections.append("_No extractable text was found in this PDF._")

    return "\n\n".join(sections).strip() + "\n"


def _extract_tables(page) -> list[str]:
    if not hasattr(page, "find_tables"):
        return []

    try:
        tables = page.find_tables()
    except Exception:
        return []

    markdown_tables: list[str] = []
    for index, table in enumerate(tables, start=1):
        rows = table.extract()
        markdown = _rows_to_markdown_table(rows)
        if markdown:
            markdown_tables.append(f"### Table {index}\n\n{markdown}")
    return markdown_tables


def _rows_to_markdown_table(rows: list[list[object]]) -> str:
    normalized = [
        [_clean_cell(cell) for cell in row]
        for row in rows
        if row and any(_clean_cell(cell) for cell in row)
    ]
    if not normalized:
        return ""

    width = max(len(row) for row in normalized)
    padded = [row + [""] * (width - len(row)) for row in normalized]
    header = padded[0]
    body = padded[1:] or [[""] * width]

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in range(width)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines)


def _clean_cell(cell: object) -> str:
    text = "" if cell is None else str(cell)
    return " ".join(text.replace("|", "\\|").split())
