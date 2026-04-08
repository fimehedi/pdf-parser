from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from app.models import BBox, Confidence, Table, TableCell
from app.ocr.tesseract_engine import ocr_tesseract


@dataclass(frozen=True)
class DetectedTable:
    bbox: BBox
    grid_quality: float


def _bbox(x0: int, y0: int, x1: int, y1: int) -> BBox:
    return BBox(x0=float(x0), y0=float(y0), x1=float(x1), y1=float(y1))


def detect_tables_from_lines(binary_page: np.ndarray) -> list[DetectedTable]:
    """
    Heuristic table detection for scanned pages.
    Returns candidate table bboxes and a coarse grid-quality score.
    """
    inv = 255 - binary_page
    h, w = inv.shape[:2]

    # Extract horizontal and vertical lines
    hor_k = max(20, w // 40)
    ver_k = max(20, h // 40)
    horizontal = cv2.erode(inv, cv2.getStructuringElement(cv2.MORPH_RECT, (hor_k, 1)), iterations=1)
    horizontal = cv2.dilate(horizontal, cv2.getStructuringElement(cv2.MORPH_RECT, (hor_k, 1)), iterations=1)
    vertical = cv2.erode(inv, cv2.getStructuringElement(cv2.MORPH_RECT, (1, ver_k)), iterations=1)
    vertical = cv2.dilate(vertical, cv2.getStructuringElement(cv2.MORPH_RECT, (1, ver_k)), iterations=1)

    grid = cv2.bitwise_or(horizontal, vertical)
    grid = cv2.dilate(grid, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), iterations=2)

    contours, _ = cv2.findContours((grid > 0).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    tables: list[DetectedTable] = []
    for c in contours:
        x, y, ww, hh = cv2.boundingRect(c)
        area = ww * hh
        if area < 0.03 * (w * h):
            continue
        if ww < 200 or hh < 120:
            continue
        crop = grid[y : y + hh, x : x + ww]
        density = float(np.mean((crop > 0).astype(np.float32)))
        # Prefer "grid-like" regions: moderate density but not full black.
        quality = max(0.0, min(1.0, (density - 0.02) / 0.18))
        tables.append(DetectedTable(bbox=_bbox(x, y, x + ww, y + hh), grid_quality=quality))
    tables.sort(key=lambda t: (t.bbox.y0, t.bbox.x0))
    return tables


def extract_table_cells_simple(
    page_gray_or_binary: np.ndarray,
    table_bbox: BBox,
    tesseract_lang: str,
) -> tuple[list[TableCell], int, int, float]:
    """
    Minimal cell extraction:
    - Attempt to derive grid intersections from detected lines.
    - If grid fails, fall back to a single-cell table with OCR of the region.
    Returns (cells, n_rows, n_cols, structure_score).
    """
    img = page_gray_or_binary
    if len(img.shape) != 2:
        raise ValueError("expected grayscale/binary image")
    x0, y0, x1, y1 = map(int, [table_bbox.x0, table_bbox.y0, table_bbox.x1, table_bbox.y1])
    crop = img[max(0, y0) : max(0, y1), max(0, x0) : max(0, x1)]
    if crop.size == 0:
        return [], 0, 0, 0.0

    # Ensure binary-ish for line detection
    if crop.dtype != np.uint8:
        crop = crop.astype(np.uint8)
    if np.mean(crop) < 127:
        bin_crop = 255 - crop
    else:
        _, bin_crop = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        bin_crop = 255 - bin_crop

    hh, ww = bin_crop.shape[:2]
    hor_k = max(15, ww // 30)
    ver_k = max(15, hh // 30)
    horizontal = cv2.erode(bin_crop, cv2.getStructuringElement(cv2.MORPH_RECT, (hor_k, 1)), iterations=1)
    horizontal = cv2.dilate(horizontal, cv2.getStructuringElement(cv2.MORPH_RECT, (hor_k, 1)), iterations=1)
    vertical = cv2.erode(bin_crop, cv2.getStructuringElement(cv2.MORPH_RECT, (1, ver_k)), iterations=1)
    vertical = cv2.dilate(vertical, cv2.getStructuringElement(cv2.MORPH_RECT, (1, ver_k)), iterations=1)

    # Line positions (project)
    hproj = np.mean((horizontal > 0).astype(np.float32), axis=1)
    vproj = np.mean((vertical > 0).astype(np.float32), axis=0)

    def pick_lines(proj: np.ndarray, min_sep: int) -> list[int]:
        idx = np.where(proj > 0.25)[0].tolist()
        if not idx:
            return []
        lines = [idx[0]]
        for i in idx[1:]:
            if i - lines[-1] >= min_sep:
                lines.append(i)
        return lines

    ys = pick_lines(hproj, min_sep=max(12, hh // 40))
    xs = pick_lines(vproj, min_sep=max(12, ww // 40))

    # Need at least a 2x2 grid => 3 lines each direction; be lenient.
    if len(xs) < 2 or len(ys) < 2:
        o = ocr_tesseract(255 - bin_crop, lang=tesseract_lang, psm=6)
        text = o.text.strip()
        return [TableCell(row=0, col=0, text=text)], 1, 1, 0.2

    # Create cells between adjacent lines
    # Add borders if missing
    if xs[0] > 3:
        xs = [0] + xs
    if xs[-1] < ww - 3:
        xs = xs + [ww - 1]
    if ys[0] > 3:
        ys = [0] + ys
    if ys[-1] < hh - 3:
        ys = ys + [hh - 1]

    cells: list[TableCell] = []
    for r in range(len(ys) - 1):
        for c in range(len(xs) - 1):
            cx0, cx1 = xs[c], xs[c + 1]
            cy0, cy1 = ys[r], ys[r + 1]
            pad = 2
            cell_img = crop[max(0, cy0 + pad) : max(0, cy1 - pad), max(0, cx0 + pad) : max(0, cx1 - pad)]
            if cell_img.size == 0:
                cell_text = ""
            else:
                o = ocr_tesseract(cell_img, lang=tesseract_lang, psm=6)
                cell_text = o.text.strip().replace("\n", " ")
            cells.append(TableCell(row=r, col=c, text=cell_text))

    n_rows = len(ys) - 1
    n_cols = len(xs) - 1
    structure_score = max(0.0, min(1.0, (min(n_rows, 20) / 6.0) * (min(n_cols, 20) / 6.0)))
    return cells, n_rows, n_cols, structure_score


def table_to_csv_matrix(cells: list[TableCell], n_rows: int, n_cols: int) -> list[list[str]]:
    mat = [["" for _ in range(n_cols)] for _ in range(n_rows)]
    for cell in cells:
        if cell.row < n_rows and cell.col < n_cols:
            mat[cell.row][cell.col] = cell.text
    return mat


def make_table_model(
    table_id: str,
    page_index: int,
    bbox: BBox,
    csv_path: str,
    method: str,
    grid_quality: float,
    structure_score: float,
    n_rows: int,
    n_cols: int,
    cells: list[TableCell],
    ocr_mean_conf: float,
) -> Table:
    score = max(0.0, min(1.0, 0.45 * grid_quality + 0.35 * structure_score + 0.20 * ocr_mean_conf))
    return Table(
        table_id=table_id,
        page_index=page_index,
        bbox=bbox,
        n_rows=n_rows,
        n_cols=n_cols,
        cells=cells,
        csv_path=csv_path,
        method=method,
        confidence=Confidence(
            score=score,
            method="table_conf_v1",
            signals={
                "grid_quality": grid_quality,
                "structure_score": structure_score,
                "ocr_mean_conf": ocr_mean_conf,
            },
        ),
    )

