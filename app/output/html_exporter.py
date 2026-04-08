from __future__ import annotations

from html import escape
from pathlib import Path

from app.models import CanonicalDocument


def export_html(doc: CanonicalDocument, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    blocks_by_page: dict[int, list] = {}
    for b in doc.blocks:
        blocks_by_page.setdefault(b.page_index, []).append(b)

    parts: list[str] = []
    parts.append("<!doctype html>")
    parts.append("<html><head><meta charset='utf-8'/>")
    parts.append("<meta name='viewport' content='width=device-width, initial-scale=1'/>")
    parts.append("<title>Parsed Document</title>")
    parts.append(
        "<style>"
        "body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;max-width:920px;margin:32px auto;padding:0 16px;}"
        ".meta{color:#444;font-size:14px;margin-bottom:18px;}"
        ".block{margin:10px 0;line-height:1.5;}"
        ".badge{display:inline-block;padding:2px 8px;border-radius:999px;background:#f1f5f9;color:#0f172a;font-size:12px;margin-left:8px;}"
        "h2{margin-top:28px;border-top:1px solid #e5e7eb;padding-top:18px;}"
        "</style>"
    )
    parts.append("</head><body>")
    parts.append("<h1>Parsed Document</h1>")
    parts.append(
        f"<div class='meta'>Source: <code>{escape(doc.source.input_path)}</code> "
        f"• Pages: <b>{doc.metadata.page_count}</b> "
        f"• Overall confidence: <b>{doc.confidence.overall.score:.2f}</b></div>"
    )

    for pi in range(doc.metadata.page_count):
        parts.append(f"<h2>Page {pi + 1}</h2>")
        page_blocks = sorted(blocks_by_page.get(pi, []), key=lambda b: b.reading_order)
        for b in page_blocks:
            text = escape(b.text.strip())
            if not text:
                continue
            badge = f"<span class='badge'>{b.type} • {b.confidence.score:.2f}</span>"
            if b.type == "heading":
                parts.append(f"<h3 class='block'>{text}{badge}</h3>")
            elif b.type == "list_item":
                parts.append(f"<div class='block'>• {text}{badge}</div>")
            else:
                parts.append(f"<div class='block'>{text}{badge}</div>")
    parts.append("</body></html>")
    p.write_text("\n".join(parts), encoding="utf-8")
    return p

