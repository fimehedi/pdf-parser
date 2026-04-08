from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.models import Block, CanonicalDocument


def export_review_tasks(doc: CanonicalDocument, path: str | Path) -> Path:
    """
    Export low-confidence blocks for human review.
    Format: simple JSON list, compatible with adapting to Label Studio.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    tasks: list[dict[str, Any]] = []
    for b in doc.blocks:
        if not bool(b.derived.get("review_required", False)):
            continue
        tasks.append(
            {
                "block_id": b.block_id,
                "page_index": b.page_index,
                "bbox": b.bbox.model_dump(),
                "text": b.text,
                "confidence": b.confidence.model_dump(),
                "candidates": b.derived.get("ocr_candidates", []),
            }
        )

    p.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    return p

