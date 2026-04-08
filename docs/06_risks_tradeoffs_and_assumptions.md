## Risks, tradeoffs, assumptions

### Risks
- **Low-quality scans**: blur/noise can destroy OCR accuracy.
- **Complex layouts**: sidebars, rotated text, and embedded images confuse reading order.
- **Tables without clear grid lines**: image-based detection may miss them.

### Tradeoffs (v1)
- Prefer robustness and traceability over perfect semantic structuring.
- Heuristic layout and table detection to avoid heavy ML dependencies in v1.

### Assumptions
- Most pages are 1–2 columns.
- Bengali + English are the primary languages.
- Tesseract Bengali model is available on the target system.

