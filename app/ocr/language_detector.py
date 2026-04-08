from __future__ import annotations


def detect_script_mix(text: str) -> dict[str, float]:
    """
    Very lightweight script detection:
    - Bengali block: U+0980..U+09FF
    - Latin letters as proxy for English
    Returns proportions in [0,1].
    """
    if not text:
        return {"bn": 0.0, "en": 0.0, "other": 0.0}

    bn = 0
    en = 0
    other = 0
    for ch in text:
        o = ord(ch)
        if 0x0980 <= o <= 0x09FF:
            bn += 1
        elif ("A" <= ch <= "Z") or ("a" <= ch <= "z"):
            en += 1
        elif ch.isspace() or ch.isdigit() or ch in ".,;:!?()[]{}'\"-–—/\\|":
            # ignore common separators from "other" to avoid noise
            continue
        else:
            other += 1
    total = max(bn + en + other, 1)
    return {"bn": bn / total, "en": en / total, "other": other / total}


def choose_ocr_lang(tesseract_langs: list[str]) -> str:
    # For mixed textbooks, default to combined languages (ben+eng) if available.
    if "ben" in tesseract_langs and "eng" in tesseract_langs:
        return "ben+eng"
    return "+".join(tesseract_langs) if tesseract_langs else "eng"

