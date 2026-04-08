from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
import pytesseract
from PIL import Image

from app.models import BBox, Confidence, TextSpan

_tess = os.environ.get("TESSERACT_CMD") or os.environ.get("TESSERACT_PATH")
if _tess:
    pytesseract.pytesseract.tesseract_cmd = _tess


@dataclass(frozen=True)
class TesseractResult:
    text: str
    spans: list[TextSpan]
    confidence: Confidence


def _norm_conf(c: str | int | float) -> float:
    try:
        v = float(c)
    except Exception:
        return 0.0
    if v < 0:
        return 0.0
    return max(0.0, min(1.0, v / 100.0))


def ocr_tesseract(
    image: np.ndarray,
    lang: str,
    psm: int = 6,
    oem: int = 1,
    config_extra: str = "",
) -> TesseractResult:
    pil = Image.fromarray(image)
    config = f"--oem {oem} --psm {psm} {config_extra}".strip()
    data = pytesseract.image_to_data(pil, lang=lang, config=config, output_type=pytesseract.Output.DICT)

    n = len(data.get("text", []))
    spans: list[TextSpan] = []
    texts: list[str] = []
    confs: list[float] = []
    for i in range(n):
        t = (data["text"][i] or "").strip()
        if not t:
            continue
        x, y, w, h = int(data["left"][i]), int(data["top"][i]), int(data["width"][i]), int(data["height"][i])
        c = _norm_conf(data["conf"][i])
        spans.append(
            TextSpan(
                text=t,
                bbox=BBox(x0=float(x), y0=float(y), x1=float(x + w), y1=float(y + h)),
                lang=None,
                confidence=Confidence(score=c, method="tesseract_word_conf", signals={}),
            )
        )
        texts.append(t)
        confs.append(c)

    joined = " ".join(texts).strip()
    mean_conf = float(sum(confs) / max(len(confs), 1)) if confs else 0.0
    low_ratio = float(sum(1 for c in confs if c < 0.5) / max(len(confs), 1)) if confs else 1.0
    overall = Confidence(
        score=mean_conf * (1.0 - 0.35 * low_ratio),
        method="tesseract_mean_word_conf_v1",
        signals={"mean_word_conf": mean_conf, "low_word_ratio": low_ratio, "n_words": len(confs)},
    )
    return TesseractResult(text=joined, spans=spans, confidence=overall)

