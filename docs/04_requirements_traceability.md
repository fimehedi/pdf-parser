## Requirements traceability (v1)

| Requirement | Implementation | Output Evidence |
|---|---|---|
| PDF ingestion + rendering | `app/pipeline.py` (PyMuPDF render) | `out/artifacts/page_XXXX.png` |
| Preprocessing (deskew/threshold) | `app/preprocessing/image_cleaner.py` | `out/artifacts/page_XXXX_pre.png` |
| BN+EN OCR with confidence | `app/ocr/tesseract_engine.py` | `blocks[].spans[].confidence` |
| Layout blocks + reading order | `app/layout/simple_layout.py` | `blocks[].reading_order`, `blocks[].bbox` |
| Table detection + CSV export | `app/tables/image_table_extractor.py` | `out/tables/*.csv`, `tables[]` |
| Multiple export formats | `app/output/*` | `out/document.json|md|html` |
| Confidence scoring | `app/confidence.py` | `document.confidence.*` |

