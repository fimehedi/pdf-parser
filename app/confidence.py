from __future__ import annotations

from app.models import Confidence


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def confidence_from_ocr(mean_block_conf: float, low_block_ratio: float, blur_score: float | None) -> Confidence:
    blur_penalty = 0.0
    if blur_score is not None:
        # Laplacian variance: higher=sharper. Penalize very blurry scans.
        blur_penalty = 0.25 if blur_score < 60 else (0.12 if blur_score < 100 else 0.0)
    score = clamp01(mean_block_conf * (1.0 - 0.35 * low_block_ratio) - blur_penalty)
    return Confidence(
        score=score,
        method="ocr_conf_v1",
        signals={
            "mean_block_conf": float(mean_block_conf),
            "low_block_ratio": float(low_block_ratio),
            "blur_score": None if blur_score is None else float(blur_score),
            "blur_penalty": float(blur_penalty),
        },
    )


def confidence_from_layout(n_blocks: int, n_cols: int, overlap_ratio: float) -> Confidence:
    # More blocks helps confidence; overlaps hurt.
    blocks_term = clamp01(min(1.0, n_blocks / 25.0))
    cols_term = 1.0 if n_cols in (1, 2) else 0.6
    score = clamp01(0.55 * blocks_term + 0.35 * cols_term + 0.10 * (1.0 - overlap_ratio))
    return Confidence(
        score=score,
        method="layout_conf_v1",
        signals={"n_blocks": n_blocks, "n_cols": n_cols, "overlap_ratio": float(overlap_ratio)},
    )


def confidence_from_images(n_images: int, caption_link_rate: float) -> Confidence:
    # If no images detected, don't punish too hard.
    if n_images == 0:
        score = 0.75
    else:
        score = clamp01(0.55 + 0.45 * caption_link_rate)
    return Confidence(
        score=score,
        method="images_conf_v1",
        signals={"n_images": n_images, "caption_link_rate": float(caption_link_rate)},
    )


def confidence_from_tables(n_tables: int, mean_table_conf: float | None) -> Confidence:
    if n_tables == 0:
        score = 0.75
    else:
        score = clamp01(mean_table_conf or 0.0)
    return Confidence(
        score=score,
        method="tables_conf_v1",
        signals={"n_tables": n_tables, "mean_table_conf": None if mean_table_conf is None else float(mean_table_conf)},
    )


def confidence_from_semantic(heuristic_score: float) -> Confidence:
    return Confidence(score=clamp01(heuristic_score), method="semantic_conf_v1", signals={})


def confidence_overall(components: dict[str, Confidence]) -> Confidence:
    w = {"ocr": 0.45, "layout": 0.20, "tables": 0.15, "images": 0.05, "semantic": 0.15}
    s = 0.0
    for k, wk in w.items():
        s += wk * float(components.get(k, Confidence(score=0.0, method="missing")).score)
    return Confidence(score=clamp01(s), method="overall_weighted_v1", signals={"weights": w})

