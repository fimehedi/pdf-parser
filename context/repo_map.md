## Repo map

### Code
- `app/pipeline.py`: end-to-end parse pipeline (PDF → outputs)
- `app/preprocessing/image_cleaner.py`: grayscale/denoise/threshold/deskew
- `app/layout/simple_layout.py`: coarse block + column heuristics
- `app/ocr/tesseract_engine.py`: BN+EN OCR with word-level confidence
- `app/ocr/easyocr_engine.py`: optional alternative OCR engine
- `app/tables/image_table_extractor.py`: image-based table detection + CSV export
- `app/output/*`: exporters (JSON/Markdown/HTML/CSV)
- `app/confidence.py`: confidence scoring aggregation

### Planning
- `docs/`: PRD, architecture, data flow, confidence scoring, test/deploy plans
- `context/`: principles, policies, constraints
- `schemas/`: canonical JSON schema(s)
- `configs/`: YAML config defaults

### Ops
- `scripts/run_plan.sh`: validates schemas
- `scripts/run_parse.sh`: installs deps + runs parser

