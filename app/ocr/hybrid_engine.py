from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

from app.models import Confidence, TextSpan
from app.ocr.easyocr_engine import ocr_easyocr
from app.ocr.google_vision_engine import ocr_google_vision
from app.ocr.tesseract_engine import ocr_tesseract


@dataclass(frozen=True)
class EngineOutput:
    engine: str
    text: str
    spans: list[TextSpan]
    confidence: Confidence
    error: str | None = None


@dataclass(frozen=True)
class HybridOCRResult:
    chosen: EngineOutput
    candidates: list[EngineOutput]
    approved: bool
    threshold: float


def _safe_call(engine: str, fn, *args, **kwargs) -> EngineOutput:
    try:
        r = fn(*args, **kwargs)
        return EngineOutput(engine=engine, text=r.text, spans=r.spans, confidence=r.confidence, error=None)
    except Exception as e:
        return EngineOutput(
            engine=engine,
            text="",
            spans=[],
            confidence=Confidence(score=0.0, method=f"{engine}_error", signals={"error": str(e)}),
            error=str(e),
        )


def run_hybrid_ocr(
    image: np.ndarray,
    engines: list[str],
    threshold: float,
    tesseract_lang: str,
    easyocr_langs: list[str],
    easyocr_gpu: bool = False,
    tesseract_psm: int = 6,
    tesseract_oem: int = 1,
    tesseract_config_extra: str = "",
) -> HybridOCRResult:
    """
    Run multiple OCR engines and choose the highest-confidence result.
    Engines supported: "google_vision", "tesseract", "easyocr"
    Missing deps/credentials are handled by producing an error candidate with 0 confidence.
    """
    tasks: list[tuple[str, object, tuple, dict]] = []
    for e in engines:
        if e == "google_vision":
            tasks.append(("google_vision", ocr_google_vision, (image,), {}))
        elif e == "tesseract":
            tasks.append(
                (
                    "tesseract",
                    ocr_tesseract,
                    (image,),
                    {"lang": tesseract_lang, "psm": tesseract_psm, "oem": tesseract_oem, "config_extra": tesseract_config_extra},
                )
            )
        elif e == "easyocr":
            tasks.append(("easyocr", ocr_easyocr, (image,), {"languages": easyocr_langs, "gpu": easyocr_gpu}))

    candidates: list[EngineOutput] = []
    if not tasks:
        fallback = EngineOutput(
            engine="none",
            text="",
            spans=[],
            confidence=Confidence(score=0.0, method="no_engines_configured", signals={}),
            error="no engines configured",
        )
        return HybridOCRResult(chosen=fallback, candidates=[fallback], approved=False, threshold=threshold)

    with ThreadPoolExecutor(max_workers=min(3, len(tasks))) as ex:
        futs = [ex.submit(_safe_call, name, fn, *args, **kwargs) for (name, fn, args, kwargs) in tasks]
        for f in as_completed(futs):
            candidates.append(f.result())

    # Choose best by confidence; tie-breaker by longer text.
    candidates.sort(key=lambda c: (c.confidence.score, len(c.text)), reverse=True)
    chosen = candidates[0]
    approved = float(chosen.confidence.score) >= float(threshold)
    return HybridOCRResult(chosen=chosen, candidates=candidates, approved=approved, threshold=threshold)

