## Architecture overview

### High-level diagram

```mermaid
flowchart LR
  A[Input PDF] --> B[Render pages to images]
  B --> C[Preprocess: denoise/threshold/deskew]
  C --> D[Layout: block detection + columns]
  D --> E[OCR: BN+EN per block]
  C --> F[Table detection (grid/lines)]
  F --> G[Cell OCR + CSV export]
  E --> H[Canonical IR (JSON model)]
  G --> H
  H --> J[Export: JSON]
  H --> K[Export: Markdown]
  H --> L[Export: HTML]
  H --> M[Confidence scoring (per stage + overall)]
```

### Module breakdown
- **Ingestion/render**: `app/pipeline.py` (PyMuPDF)
- **Preprocessing**: `app/preprocessing/image_cleaner.py` (OpenCV)
- **Layout**: `app/layout/simple_layout.py` (OpenCV morphology + CC)
- **OCR**: `app/ocr/tesseract_engine.py` (word conf), `app/ocr/easyocr_engine.py` (optional)
- **Tables**: `app/tables/image_table_extractor.py` (grid-based)
- **Confidence**: `app/confidence.py`
- **Export**: `app/output/*`
- **CLI**: `app/cli.py`

