from __future__ import annotations

import json
from pathlib import Path

from app.models import CanonicalDocument


def export_json(doc: CanonicalDocument, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    return p

