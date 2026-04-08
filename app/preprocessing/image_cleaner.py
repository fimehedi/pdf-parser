from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class PreprocessSignals:
    deskew_angle_deg: float | None
    blur_score: float | None
    dewarp_applied: bool


def _variance_of_laplacian(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _order_points(pts: np.ndarray) -> np.ndarray:
    # pts: (4,2)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).reshape(-1)
    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]
    return np.array([tl, tr, br, bl], dtype=np.float32)


def dewarp_perspective(gray: np.ndarray) -> tuple[np.ndarray, bool]:
    """
    Simple 'dewarp' via page contour detection + 4-point perspective transform.
    This corrects keystone/perspective distortion (not full curved-page dewarping).
    """
    if len(gray.shape) != 2:
        raise ValueError("expected grayscale image")
    h, w = gray.shape[:2]
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    edges = cv2.dilate(edges, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)), iterations=1)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return gray, False
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) != 4:
            continue
        pts = approx.reshape(4, 2).astype(np.float32)
        rect = _order_points(pts)
        (tl, tr, br, bl) = rect
        widthA = np.linalg.norm(br - bl)
        widthB = np.linalg.norm(tr - tl)
        heightA = np.linalg.norm(tr - br)
        heightB = np.linalg.norm(tl - bl)
        maxW = int(max(widthA, widthB))
        maxH = int(max(heightA, heightB))
        if maxW < 0.5 * w or maxH < 0.5 * h:
            continue
        dst = np.array([[0, 0], [maxW - 1, 0], [maxW - 1, maxH - 1], [0, maxH - 1]], dtype=np.float32)
        m = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(gray, m, (maxW, maxH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return warped, True
    return gray, False


def deskew_binarized(binary: np.ndarray) -> tuple[np.ndarray, float | None]:
    coords = np.column_stack(np.where(binary > 0))
    if coords.size < 2000:
        return binary, None
    rect = cv2.minAreaRect(coords.astype(np.float32))
    angle = rect[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) < 0.2:
        return binary, 0.0
    (h, w) = binary.shape[:2]
    center = (w // 2, h // 2)
    m = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(binary, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated, float(angle)


def preprocess_page(bgr: np.ndarray, profile: str = "default") -> tuple[np.ndarray, PreprocessSignals]:
    """
    profile:
      - default: balanced for mixed scans
      - bangla_scan: slightly stronger denoise + finer adaptive threshold (helps Indic + small type)
    """
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blur_score = _variance_of_laplacian(gray)
    gray2, dewarped = dewarp_perspective(gray)
    if profile == "bangla_scan":
        den = cv2.fastNlMeansDenoising(gray2, None, h=15, templateWindowSize=7, searchWindowSize=21)
        thr = cv2.adaptiveThreshold(
            den,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            9,
        )
    else:
        den = cv2.fastNlMeansDenoising(gray2, None, h=12, templateWindowSize=7, searchWindowSize=21)
        thr = cv2.adaptiveThreshold(
            den,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            35,
            11,
        )
    inv = 255 - thr
    inv2, angle = deskew_binarized(inv)
    out = 255 - inv2
    return out, PreprocessSignals(deskew_angle_deg=angle, blur_score=blur_score, dewarp_applied=dewarped)

