from __future__ import annotations

from pathlib import Path

from app.models import CanonicalDocument


def export_markdown(doc: CanonicalDocument, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append(f"# Parsed Document")
    lines.append("")
    lines.append(f"- Source: `{doc.source.input_path}`")
    lines.append(f"- Pages: **{doc.metadata.page_count}**")
    lines.append(f"- Languages: **{', '.join(doc.metadata.languages)}**")
    lines.append(f"- Confidence (overall): **{doc.confidence.overall.score:.2f}**")
    lines.append("")

    blocks_by_page: dict[int, list] = {}
    for b in doc.blocks:
        blocks_by_page.setdefault(b.page_index, []).append(b)
    for pi in range(doc.metadata.page_count):
        lines.append(f"## Page {pi + 1}")
        lines.append("")
        page_blocks = sorted(blocks_by_page.get(pi, []), key=lambda b: b.reading_order)
        for b in page_blocks:
            t = b.text.strip()
            if not t:
                continue
            if b.type == "heading":
                lines.append(f"### {t}")
            elif b.type == "list_item":
                lines.append(f"- {t}")
            else:
                lines.append(t)
            lines.append("")

    p.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return p

