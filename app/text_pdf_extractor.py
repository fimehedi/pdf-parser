from __future__ import annotations

from dataclasses import dataclass

import fitz  # PyMuPDF

from app.models import BBox, Block, Confidence, TextSpan


@dataclass(frozen=True)
class TextPdfSignals:
    has_text: bool
    total_chars: int


def detect_text_pdf(doc: fitz.Document, min_chars_per_page: int = 30, min_ratio: float = 0.6) -> bool:
    """
    Heuristic: if most pages have selectable text above a threshold, treat as text-based.
    """
    if doc.page_count == 0:
        return False
    pages_with_text = 0
    for i in range(doc.page_count):
        t = (doc.load_page(i).get_text("text") or "").strip()
        if len(t) >= min_chars_per_page:
            pages_with_text += 1
    return (pages_with_text / doc.page_count) >= min_ratio


def extract_text_blocks_from_page(page: fitz.Page, page_index: int) -> tuple[list[Block], TextPdfSignals]:
    """
    Extract text blocks without OCR using PyMuPDF's block segmentation.
    """
    blocks: list[Block] = []
    raw_blocks = page.get_text("blocks")  # (x0, y0, x1, y1, "text", block_no, block_type)
    reading_order = 0
    total_chars = 0

    for b in raw_blocks:
        x0, y0, x1, y1, text = float(b[0]), float(b[1]), float(b[2]), float(b[3]), str(b[4] or "")
        text = text.strip()
        if not text:
            continue
        total_chars += len(text)
        bbox = BBox(x0=x0, y0=y0, x1=x1, y1=y1)
        conf = Confidence(score=1.0, method="native_pdf_text", signals={})
        span = TextSpan(text=text, bbox=bbox, lang=None, confidence=conf)
        blocks.append(
            Block(
                block_id=f"b_{page_index:04d}_{reading_order:04d}",
                page_index=page_index,
                type="paragraph",
                bbox=bbox,
                reading_order=reading_order,
                column_index=None,
                text=text,
                spans=[span],
                confidence=conf,
                derived={"source": "native_text"},
            )
        )
        reading_order += 1

    has_text = total_chars > 0
    return blocks, TextPdfSignals(has_text=has_text, total_chars=total_chars)

