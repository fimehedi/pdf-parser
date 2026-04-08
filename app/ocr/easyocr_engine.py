from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.models import BBox, Confidence, TextSpan


@dataclass(frozen=True)
class EasyOCRResult:
    text: str
    spans: list[TextSpan]
    confidence: Confidence


_READER_CACHE: dict[tuple[tuple[str, ...], bool], object] = {}


def _get_reader(languages: list[str], gpu: bool) -> object:
    # Lazy import to keep startup fast.
    import easyocr  # type: ignore

    key = (tuple(languages), bool(gpu))
    if key in _READER_CACHE:
        return _READER_CACHE[key]
    reader = easyocr.Reader(languages, gpu=gpu, verbose=False)
    _READER_CACHE[key] = reader
    return reader


def ocr_easyocr(
    image: np.ndarray,
    languages: list[str],
    gpu: bool = False,
    readtext_kwargs: dict | None = None,
) -> EasyOCRResult:
    reader = _get_reader(languages, gpu=gpu)
    # result: list[[bbox4], text, conf]
    kw = dict(readtext_kwargs or {})
    if "batch_size" not in kw and gpu:
        kw["batch_size"] = 8
    result = reader.readtext(image, **kw)
    spans: list[TextSpan] = []
    texts: list[str] = []
    confs: list[float] = []
    for bbox4, text, conf in result:
        if not text:
            continue
        xs = [p[0] for p in bbox4]
        ys = [p[1] for p in bbox4]
        x0, x1 = float(min(xs)), float(max(xs))
        y0, y1 = float(min(ys)), float(max(ys))
        c = max(0.0, min(1.0, float(conf)))
        spans.append(
            TextSpan(
                text=text,
                bbox=BBox(x0=x0, y0=y0, x1=x1, y1=y1),
                lang=None,
                confidence=Confidence(score=c, method="easyocr_line_conf", signals={}),
            )
        )
        texts.append(text)
        confs.append(c)
    joined = "\n".join(texts).strip()
    mean_conf = float(sum(confs) / max(len(confs), 1)) if confs else 0.0
    overall = Confidence(
        score=mean_conf,
        method="easyocr_mean_conf_v1",
        signals={"mean_line_conf": mean_conf, "n_lines": len(confs)},
    )
    return EasyOCRResult(text=joined, spans=spans, confidence=overall)

