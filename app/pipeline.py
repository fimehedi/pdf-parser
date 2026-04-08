from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

import cv2
import fitz  # PyMuPDF
import numpy as np

from app.confidence import (
    confidence_from_images,
    confidence_from_layout,
    confidence_from_ocr,
    confidence_from_semantic,
    confidence_from_tables,
    confidence_overall,
)
from app.layout.simple_layout import detect_text_blocks
from app.models import (
    BBox,
    Block,
    CanonicalDocument,
    Confidence,
    ConfidenceSummary,
    Exports,
    ExtractedImage,
    Metadata,
    Page,
    Source,
)
from app.ocr.language_detector import choose_ocr_lang
from app.ocr.hybrid_engine import run_hybrid_ocr
from app.preprocessing.image_cleaner import preprocess_page
from app.tables.image_table_extractor import (
    detect_tables_from_lines,
    extract_table_cells_simple,
    make_table_model,
    table_to_csv_matrix,
)
from app.text_pdf_extractor import detect_text_pdf, extract_text_blocks_from_page
from app.config import load_yaml

log = logging.getLogger(__name__)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _crop(img: np.ndarray, bbox: BBox) -> np.ndarray:
    x0, y0, x1, y1 = map(int, [bbox.x0, bbox.y0, bbox.x1, bbox.y1])
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(img.shape[1], x1)
    y1 = min(img.shape[0], y1)
    return img[y0:y1, x0:x1]


def _overlap_ratio(blocks: list[Block]) -> float:
    # Very rough overlap estimate: how many pairs overlap significantly.
    if len(blocks) < 2:
        return 0.0
    overlaps = 0
    pairs = 0
    for i in range(len(blocks)):
        a = blocks[i].bbox
        for j in range(i + 1, len(blocks)):
            b = blocks[j].bbox
            pairs += 1
            ix0 = max(a.x0, b.x0)
            iy0 = max(a.y0, b.y0)
            ix1 = min(a.x1, b.x1)
            iy1 = min(a.y1, b.y1)
            iw = max(0.0, ix1 - ix0)
            ih = max(0.0, iy1 - iy0)
            inter = iw * ih
            if inter <= 0:
                continue
            area_a = max(1.0, (a.x1 - a.x0) * (a.y1 - a.y0))
            if inter / area_a > 0.25:
                overlaps += 1
    return float(overlaps / max(pairs, 1))


def parse_pdf(
    input_pdf: str | Path,
    out_dir: str | Path,
    dpi: int = 300,
    tesseract_langs: list[str] | None = None,
    use_ocr: bool | None = None,
    ocr_config_path: str | Path | None = None,
) -> CanonicalDocument:
    input_pdf = Path(input_pdf)
    out_dir = Path(out_dir)
    artifacts_dir = out_dir / "artifacts"
    images_dir = out_dir / "images"
    tables_dir = out_dir / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    tesseract_langs = tesseract_langs or ["ben", "eng"]
    tess_lang = choose_ocr_lang(tesseract_langs)
    ocr_cfg = {}
    if ocr_config_path is not None:
        try:
            ocr_cfg = load_yaml(ocr_config_path)
        except Exception as e:
            log.warning("Failed to load ocr config %s: %s", ocr_config_path, e)
            ocr_cfg = {}

    easyocr_langs = (ocr_cfg.get("languages", {}) or {}).get("easyocr", ["bn", "en"])
    hybrid_engines = (ocr_cfg.get("ocr", {}) or {}).get("engines", ["google_vision", "tesseract", "easyocr"])
    hybrid_threshold = float((ocr_cfg.get("ocr", {}) or {}).get("confidence_threshold", 0.85))
    easyocr_gpu = bool(((ocr_cfg.get("easyocr", {}) or {}).get("gpu", False)))
    tess_psm = int(((ocr_cfg.get("tesseract", {}) or {}).get("psm", 6)))
    tess_oem = int(((ocr_cfg.get("tesseract", {}) or {}).get("oem", 1)))
    tess_extra = str(((ocr_cfg.get("tesseract", {}) or {}).get("config_extra", "")))

    doc = fitz.open(str(input_pdf))

    auto_is_text_pdf = detect_text_pdf(doc)
    use_ocr = (use_ocr is True) or (use_ocr is None and not auto_is_text_pdf)
    log.info("PDF mode: %s", "OCR(use_ocr=true)" if use_ocr else "Native text(use_ocr=false)")

    pages: list[Page] = []
    blocks: list[Block] = []
    tables = []
    extracted_images: list[ExtractedImage] = []

    block_confs: list[float] = []
    blur_scores: list[float] = []
    low_block_count = 0
    layout_cols_seen: set[int] = set()

    pdfplumber_pdf = None
    if not use_ocr:
        try:
            import pdfplumber  # type: ignore

            pdfplumber_pdf = pdfplumber.open(str(input_pdf))
        except Exception as e:
            log.warning("pdfplumber not available for native tables: %s", e)

    for page_index in range(doc.page_count):
        page = doc.load_page(page_index)

        if not use_ocr:
            # Native text path (no OCR, no image artifacts required)
            w = int(page.rect.width)
            h = int(page.rect.height)
            pages.append(Page(page_index=page_index, width_px=w, height_px=h, image_path="", thumbnail_path=None))
            page_blocks, signals = extract_text_blocks_from_page(page, page_index=page_index)
            blocks.extend(page_blocks)
            # Native table extraction (text-based PDFs) using pdfplumber.
            try:
                if pdfplumber_pdf is not None:
                    p = pdfplumber_pdf.pages[page_index]
                    extracted = p.extract_tables() or []
                    for ti, tbl in enumerate(extracted):
                        if not tbl:
                            continue
                        n_rows = len(tbl)
                        n_cols = max((len(r) for r in tbl if r), default=0)
                        csv_rel = Path("tables") / f"page_{page_index:04d}_table_{ti:02d}.csv"
                        csv_path = out_dir / csv_rel
                        from app.output.csv_exporter import export_csv_matrix

                        # Normalize None -> ""
                        matrix = [[("" if c is None else str(c)) for c in (row or [])] for row in tbl]
                        export_csv_matrix(matrix, csv_path)

                        # We don't have reliable table bbox from this API in v1; set page-wide bbox.
                        bbox = BBox(x0=0.0, y0=0.0, x1=float(w), y1=float(h))
                        cells = []
                        for r, row in enumerate(matrix):
                            for c, val in enumerate(row):
                                cells.append({"row": r, "col": c, "text": val})
                        from app.models import TableCell

                        cell_models = [TableCell(**c) for c in cells]
                        from app.models import Table

                        tables.append(
                            Table(
                                table_id=f"t_{page_index:04d}_{ti:02d}",
                                page_index=page_index,
                                bbox=bbox,
                                n_rows=n_rows,
                                n_cols=n_cols,
                                cells=cell_models,
                                csv_path=str(csv_rel),
                                method="pdfplumber_native_v1",
                                confidence=Confidence(score=0.95, method="native_table", signals={"use_ocr": False}),
                            )
                        )
            except Exception as e:
                log.warning("Native table extraction failed on page %s: %s", page_index, e)

            layout_cols_seen.add(1)
            blur_scores.append(999.0)
            block_confs.extend([b.confidence.score for b in page_blocks])
            continue

        # OCR path (render + preprocess + layout + OCR)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        page_img_path = artifacts_dir / f"page_{page_index:04d}.png"
        cv2.imwrite(str(page_img_path), bgr)
        pages.append(
            Page(
                page_index=page_index,
                width_px=int(pix.width),
                height_px=int(pix.height),
                image_path=str(page_img_path.relative_to(out_dir)),
                thumbnail_path=None,
            )
        )

        pre, signals = preprocess_page(bgr)
        blur_scores.append(float(signals.blur_score or 0.0))
        pre_path = artifacts_dir / f"page_{page_index:04d}_pre.png"
        cv2.imwrite(str(pre_path), pre)

        layout_blocks = detect_text_blocks(pre)
        layout_cols_seen.update({b.column_index for b in layout_blocks})

        # OCR each block
        for reading_order, lb in enumerate(layout_blocks):
            crop = _crop(pre, lb.bbox)
            hres = run_hybrid_ocr(
                crop,
                engines=hybrid_engines,
                threshold=hybrid_threshold,
                tesseract_lang=tess_lang,
                easyocr_langs=easyocr_langs,
                easyocr_gpu=easyocr_gpu,
                tesseract_psm=tess_psm,
                tesseract_oem=tess_oem,
                tesseract_config_extra=tess_extra,
            )
            text = (hres.chosen.text or "").strip()
            if not text:
                continue
            c = float(hres.chosen.confidence.score)
            block_confs.append(c)
            if c < 0.55:
                low_block_count += 1

            blocks.append(
                Block(
                    block_id=f"b_{page_index:04d}_{reading_order:04d}",
                    page_index=page_index,
                    type="paragraph",
                    bbox=lb.bbox,
                    reading_order=int(reading_order),
                    column_index=int(lb.column_index),
                    text=text,
                    spans=hres.chosen.spans,
                    confidence=hres.chosen.confidence,
                    derived={
                        "preprocess": {
                            "deskew_angle_deg": signals.deskew_angle_deg,
                            "dewarp_applied": signals.dewarp_applied,
                        },
                        "ocr_engine": hres.chosen.engine,
                        "ocr_threshold": hres.threshold,
                        "review_required": (not hres.approved),
                        "ocr_candidates": [
                            {
                                "engine": c.engine,
                                "confidence": c.confidence.model_dump(),
                                "error": c.error,
                                "text_preview": (c.text or "")[:2000],
                            }
                            for c in hres.candidates
                        ],
                    },
                )
            )

        # Table detection/extraction (image-based)
        detected = detect_tables_from_lines(pre)
        for ti, t in enumerate(detected):
            cells, n_rows, n_cols, structure_score = extract_table_cells_simple(pre, t.bbox, tesseract_lang=tess_lang)
            csv_rel = Path("tables") / f"page_{page_index:04d}_table_{ti:02d}.csv"
            csv_path = out_dir / csv_rel
            matrix = table_to_csv_matrix(cells, n_rows, n_cols)
            # write CSV
            from app.output.csv_exporter import export_csv_matrix

            export_csv_matrix(matrix, csv_path)
            ocr_mean_conf = float(np.mean([c.confidence.score for c in blocks if c.page_index == page_index])) if blocks else 0.0
            table_model = make_table_model(
                table_id=f"t_{page_index:04d}_{ti:02d}",
                page_index=page_index,
                bbox=t.bbox,
                csv_path=str(csv_rel),
                method="image_grid_v1",
                grid_quality=t.grid_quality,
                structure_score=structure_score,
                n_rows=n_rows,
                n_cols=n_cols,
                cells=cells,
                ocr_mean_conf=ocr_mean_conf,
            )
            tables.append(table_model)

    mean_block_conf = float(sum(block_confs) / max(len(block_confs), 1)) if block_confs else 0.0
    low_block_ratio = float(low_block_count / max(len(block_confs), 1)) if block_confs else 1.0
    mean_blur = float(sum(blur_scores) / max(len(blur_scores), 1)) if blur_scores else None

    layout_conf = confidence_from_layout(
        n_blocks=len(blocks),
        n_cols=len(layout_cols_seen) if layout_cols_seen else 1,
        overlap_ratio=_overlap_ratio(blocks),
    )
    if use_ocr:
        ocr_conf = confidence_from_ocr(mean_block_conf=mean_block_conf, low_block_ratio=low_block_ratio, blur_score=mean_blur)
    else:
        ocr_conf = Confidence(score=1.0, method="native_pdf_text", signals={"use_ocr": False})
    tables_conf = confidence_from_tables(
        n_tables=len(tables),
        mean_table_conf=float(sum(t.confidence.score for t in tables) / len(tables)) if tables else None,
    )
    images_conf = confidence_from_images(n_images=len(extracted_images), caption_link_rate=0.0)
    semantic_conf = confidence_from_semantic(heuristic_score=0.7)

    components = {"ocr": ocr_conf, "layout": layout_conf, "tables": tables_conf, "images": images_conf, "semantic": semantic_conf}
    overall = confidence_overall(components)
    conf_summary = ConfidenceSummary(overall=overall, components=components, notes=[])

    out_json = out_dir / "document.json"
    out_md = out_dir / "document.md"
    out_html = out_dir / "document.html"

    cd = CanonicalDocument(
        source=Source(input_path=str(input_pdf), file_type="pdf", sha256=sha256_file(input_pdf)),
        metadata=Metadata(
            created_at=datetime.now(timezone.utc).isoformat(),
            page_count=int(doc.page_count),
            languages=tesseract_langs,
        ),
        pages=pages,
        blocks=blocks,
        tables=tables,
        images=extracted_images,
        exports=Exports(
            json_path=str(out_json.relative_to(out_dir)),
            markdown_path=str(out_md.relative_to(out_dir)),
            html_path=str(out_html.relative_to(out_dir)),
            tables_dir="tables",
            images_dir="images",
        ),
        confidence=conf_summary,
    )

    # Export
    from app.output.html_exporter import export_html
    from app.output.json_exporter import export_json
    from app.output.markdown_exporter import export_markdown
    from app.output.human_review import export_review_tasks

    export_json(cd, out_json)
    export_markdown(cd, out_md)
    export_html(cd, out_html)
    export_review_tasks(cd, out_dir / "review_tasks.json")

    log.info("Exported JSON: %s", out_json)
    log.info("Exported Markdown: %s", out_md)
    log.info("Exported HTML: %s", out_html)
    if pdfplumber_pdf is not None:
        try:
            pdfplumber_pdf.close()
        except Exception:
            pass
    return cd

