from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from app.models import BBox


@dataclass(frozen=True)
class LayoutBlock:
    bbox: BBox
    column_index: int


def _bbox_from_xywh(x: int, y: int, w: int, h: int) -> BBox:
    return BBox(x0=float(x), y0=float(y), x1=float(x + w), y1=float(y + h))


def detect_text_blocks(binary_page: np.ndarray) -> list[LayoutBlock]:
    """
    Detect coarse text blocks on a (white=255, black=0) binarized page.
    Strategy: invert → close to merge characters → connected components.
    """
    if len(binary_page.shape) != 2:
        raise ValueError("binary_page must be grayscale")

    inv = 255 - binary_page
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 7))
    merged = cv2.morphologyEx(inv, cv2.MORPH_CLOSE, k, iterations=2)
    merged = cv2.dilate(merged, cv2.getStructuringElement(cv2.MORPH_RECT, (9, 3)), iterations=1)

    n, labels, stats, _ = cv2.connectedComponentsWithStats((merged > 0).astype(np.uint8), connectivity=8)
    candidates: list[tuple[int, int, int, int, int]] = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < 8000:
            continue
        if w < 60 or h < 20:
            continue
        candidates.append((x, y, w, h, area))

    if not candidates:
        return []

    # Column detection: cluster by x-center into 1 or 2 columns (simple heuristic).
    centers = np.array([x + w / 2 for x, y, w, h, a in candidates], dtype=np.float32)
    page_w = float(binary_page.shape[1])
    norm = centers / max(page_w, 1.0)
    if (np.quantile(norm, 0.75) - np.quantile(norm, 0.25)) > 0.25:
        mid = float(np.median(centers))
        col_assign = [0 if (x + w / 2) <= mid else 1 for x, y, w, h, a in candidates]
    else:
        col_assign = [0 for _ in candidates]

    blocks: list[LayoutBlock] = []
    for (x, y, w, h, _), col in zip(candidates, col_assign, strict=False):
        blocks.append(LayoutBlock(bbox=_bbox_from_xywh(x, y, w, h), column_index=int(col)))

    # Reading order: top-to-bottom, then left-to-right by column.
    blocks.sort(key=lambda b: (b.column_index, b.bbox.y0, b.bbox.x0))
    return blocks

