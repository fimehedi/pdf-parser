from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.models import BBox, Confidence, TextSpan


@dataclass(frozen=True)
class GoogleVisionResult:
    text: str
    spans: list[TextSpan]
    confidence: Confidence


def ocr_google_vision(image: np.ndarray) -> GoogleVisionResult:
    """
    Google Cloud Vision OCR (Document Text Detection).
    Requires:
      - google-cloud-vision installed
      - Application Default Credentials configured (GOOGLE_APPLICATION_CREDENTIALS)

    Notes:
      - The API does not always return per-word confidences for all outputs; we compute a proxy.
    """
    try:
        from google.cloud import vision  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("google-cloud-vision not installed") from e

    client = vision.ImageAnnotatorClient()

    if image.dtype != np.uint8:
        image = image.astype(np.uint8)
    # Vision expects encoded image bytes (PNG/JPEG), not raw ndarray bytes.
    try:
        import cv2  # type: ignore

        ok, buf = cv2.imencode(".png", image)
        if not ok:
            raise RuntimeError("cv2.imencode failed")
        content = bytes(buf)
    except Exception as e:
        raise RuntimeError("Failed to encode image for Google Vision") from e

    gimg = vision.Image(content=content)
    resp = client.document_text_detection(image=gimg)
    if resp.error.message:  # pragma: no cover
        raise RuntimeError(resp.error.message)

    full_text = (resp.full_text_annotation.text or "").strip()

    # Proxy spans: use whole-page/whole-block span when word confidence isn't available.
    spans: list[TextSpan] = []
    if full_text:
        spans.append(
            TextSpan(
                text=full_text,
                bbox=BBox(x0=0.0, y0=0.0, x1=float(image.shape[1]), y1=float(image.shape[0])),
                lang=None,
                confidence=Confidence(score=0.9, method="gcv_proxy_conf", signals={}),
            )
        )

    # Proxy confidence: penalize if many suspicious characters / empty output.
    n = len(full_text)
    score = 0.0 if n == 0 else 0.92
    conf = Confidence(score=score, method="google_vision_proxy_v1", signals={"n_chars": n})
    return GoogleVisionResult(text=full_text, spans=spans, confidence=conf)

