## PRD

### Goals
- Parse scanned PDFs into a canonical structured document model.
- Extract Bengali + English text with OCR confidence.
- Detect coarse layout (blocks + 1–2 columns) and reconstruct reading order.
- Detect scanned tables and export them as CSV with confidence.
- Export outputs in JSON/Markdown/HTML.

### Non-goals (v1)
- Perfect math formula parsing (rendered LaTeX)
- Perfect figure-caption linking for all book styles
- Fully semantic question/answer classification (beyond heuristics)

### Functional requirements
- **PDF ingestion**: accept `.pdf` path; render pages to images (configurable DPI).
- **Preprocessing**: grayscale, denoise, adaptive threshold, deskew.
- **OCR**: BN+EN OCR using Tesseract by default; record span-level confidences.
- **Layout**: detect text blocks and reading order for 1–2 columns.
- **Tables**: detect grid-like tables and extract cell text to CSV.
- **Confidence**: stage confidences + overall, plus signals for debugging.
- **Export**: JSON canonical + Markdown + HTML + CSV tables.

### Success criteria (v1)
- Produces outputs without manual intervention on typical scanned textbooks.
- Correct reading order for most 2-column pages.
- Useful confidence separation: low-confidence pages/blocks correlate with OCR errors.

