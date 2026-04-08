from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.models import Confidence, TextSpan
from app.ocr.easyocr_engine import ocr_easyocr
from app.ocr.google_vision_engine import ocr_google_vision
from app.ocr.language_detector import detect_script_mix
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


def _norm_ocr_text(t: str) -> str:
    t = (t or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t


def _text_similarity(a: str, b: str) -> float:
    a, b = _norm_ocr_text(a), _norm_ocr_text(b)
    if not a or not b:
        return 0.0
    return float(SequenceMatcher(None, a, b).ratio())


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
    easyocr_readtext: dict | None = None,
    engine_weights: dict[str, float] | None = None,
    consensus_boost: bool = True,
    consensus_min_similarity: float = 0.78,
    consensus_boost_delta: float = 0.08,
    bangla_easyocr_weight_bonus: float = 0.04,
) -> HybridOCRResult:
    """
    Run multiple OCR engines and choose the best result using weighted scores.
    When two top engines agree (text similarity), boost confidence toward 0.90+ targets.
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
            tasks.append(
                (
                    "easyocr",
                    ocr_easyocr,
                    (image,),
                    {"languages": easyocr_langs, "gpu": easyocr_gpu, "readtext_kwargs": easyocr_readtext or {}},
                )
            )

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

    max_workers = max(1, min(len(tasks), 4))
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(_safe_call, name, fn, *args, **kwargs) for (name, fn, args, kwargs) in tasks]
        for f in as_completed(futs):
            candidates.append(f.result())

    weights = engine_weights or {}

    def effective_score(c: EngineOutput) -> float:
        base = float(c.confidence.score)
        w = float(weights.get(c.engine, 1.0))
        eff = base * w
        mix = detect_script_mix(c.text or "")
        if c.engine == "easyocr" and float(mix.get("bn", 0.0)) >= 0.2:
            eff = min(1.0, eff + bangla_easyocr_weight_bonus)
        return eff

    ranked = sorted(candidates, key=lambda c: (effective_score(c), len(c.text or "")), reverse=True)
    chosen = ranked[0]

    boosted_conf = chosen.confidence
    consensus_meta: dict = {}
    if (
        consensus_boost
        and len(ranked) >= 2
        and (chosen.text or "").strip()
        and _text_similarity(ranked[0].text, ranked[1].text) >= float(consensus_min_similarity)
    ):
        top_score = max(float(ranked[0].confidence.score), float(ranked[1].confidence.score))
        new_score = min(0.98, top_score + float(consensus_boost_delta))
        boosted_conf = Confidence(
            score=new_score,
            method="hybrid_consensus_v1",
            signals={
                "engines": [ranked[0].engine, ranked[1].engine],
                "similarity": _text_similarity(ranked[0].text, ranked[1].text),
                "prior_scores": [ranked[0].confidence.score, ranked[1].confidence.score],
            },
        )
        chosen = EngineOutput(
            engine=chosen.engine,
            text=chosen.text,
            spans=chosen.spans,
            confidence=boosted_conf,
            error=chosen.error,
        )

    approved = float(chosen.confidence.score) >= float(threshold)
    return HybridOCRResult(chosen=chosen, candidates=candidates, approved=approved, threshold=threshold)
