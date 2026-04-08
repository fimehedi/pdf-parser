## Scanned Textbook PDF Processing Engine (BN+EN)

This repository contains a **PDF processing engine** for textbooks/study books, optimized for **Bengali + English** mixed pages, multi‑column layouts, and educational artifacts (questions, exercises, lesson content, tables, diagrams).

The engine supports:
- **Text-based PDFs** (no OCR): use native text extraction
- **Scanned image PDFs** (OCR): hybrid OCR (Google Vision + Tesseract + EasyOCR) with layout + table detection

### Smart OCR decision (`use_ocr`)
- **`use_ocr` omitted**: auto-detect
  - If the PDF has selectable text → **no OCR**
  - If the PDF is scanned/image-based → **OCR**
- **`use_ocr=true`**: force OCR
- **`use_ocr=false`**: force native text extraction

### Hybrid OCR (Bangla-first)
When OCR is used, each text block is processed by a **hybrid OCR pipeline**:
- **Google Cloud Vision** (optional; best Bangla accuracy in many scans)
- **Tesseract 5** (`ben+eng`)
- **EasyOCR** (`bn` + `en`)

The engine selects the **highest-confidence** output per block.
- **Auto-approve threshold**: **0.85**
- Blocks below threshold are flagged for human review and exported to:
  - `out/review_tasks.json`

---

### How it works

#### 1) PDF type detection and routing
- The parser inspects pages for **selectable text**.
- If selectable text is present on most pages, it runs the **native text path** (no OCR).
- Otherwise it runs the **scanned/OCR path**.
- You can override this behavior with `--use-ocr` / `--no-use-ocr`.

#### 2) Native text path (real PDFs, `use_ocr=false`)
- **Text extraction**: PyMuPDF block extraction (preserves Bengali Unicode).
- **Table extraction**: `pdfplumber` native table extraction → `out/tables/*.csv`.
- **Confidence**: `ocr` stage confidence is set to 1.0 with method `native_pdf_text`.

#### 3) Scanned/OCR path (image PDFs, `use_ocr=true`)
- **Render**: PyMuPDF renders each page to an image at the configured DPI.
- **Preprocess**: OpenCV preprocessing:
  - simple **dewarp** (page contour + perspective transform)
  - denoise → adaptive threshold → deskew
- **Layout**: heuristic multi-block segmentation (coarse text blocks + column grouping).
- **Hybrid OCR per block**:
  - Engines run and the best candidate is selected by confidence:
    - `google_vision` (optional)
    - `tesseract` (`ben+eng`)
    - `easyocr` (`bn`,`en`)
  - If best confidence \(< 0.85\), the block is flagged `review_required=true` and exported to `out/review_tasks.json`.
- **Tables (scanned)**: image-based grid detection + cell OCR → `out/tables/*.csv` (v1).

#### 4) Output bundle
Everything is exported under the chosen `--out` directory:
- `document.json`: canonical structured output (pages, blocks, tables, images, confidence)
- `document.md`: reading-order text
- `document.html`: review-friendly rendering with confidence badges
- `review_tasks.json`: low-confidence OCR blocks for human review (OCR path)
- `artifacts/`: rendered + preprocessed pages (OCR path)

---

### Configuration

#### Parser config
- File: `configs/parser_config.yaml`
- Key:
  - `processing.use_ocr`: `null` (auto) / `true` / `false`

#### OCR config (hybrid pipeline)
- File: `configs/ocr_config.yaml`
- Keys:
  - `ocr.engines`: list like `["google_vision","tesseract","easyocr"]`
  - `ocr.confidence_threshold`: default `0.85`
  - `languages.tesseract`: default `["ben","eng"]`
  - `languages.easyocr`: default `["bn","en"]`
  - `easyocr.gpu`: `true|false`
  - `tesseract.psm|oem|config_extra`

CLI usage:

```bash
python -m app.cli --ocr-config configs/ocr_config.yaml --input path/to/book.pdf --out out
```

---

### Local usage

#### 1. System dependencies
- Python 3.11+
- Tesseract with Bengali + English data:

```bash
brew install tesseract tesseract-lang
```

Ensure `ben` and `eng` are listed:

```bash
tesseract --list-langs | egrep 'ben|eng'
```

#### 2. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 3. Parse a PDF

- **Auto-detect mode** (use OCR only if needed):

```bash
python -m app.cli --input path/to/book.pdf --out out
```

- **Force OCR ON** (`use_ocr=true`):

```bash
python -m app.cli --input path/to/book.pdf --out out --use-ocr
```

- **Force OCR OFF** (`use_ocr=false`, native text only):

```bash
python -m app.cli --input path/to/book.pdf --out out --no-use-ocr
```

- **Use config file** (defaults: `configs/parser_config.yaml`):

```bash
python -m app.cli --config configs/parser_config.yaml --input path/to/book.pdf --out out
```

Outputs:
- `out/document.json` – canonical structured output (blocks/tables/images + confidence)
- `out/document.md` – readable Markdown
- `out/document.html` – HTML with confidence badges
- `out/tables/*.csv` – extracted tables
  - text-based PDFs: native table extraction via `pdfplumber`
  - scanned PDFs: OCR-based grid table extraction (v1)
- `out/artifacts/*.png` – rendered + preprocessed pages (OCR path only)
- `out/review_tasks.json` – low-confidence OCR blocks for human review (OCR path only)

---

### Docker usage

Build image (default, lightweight: **Tesseract-only**, no EasyOCR/Torch):

```bash
docker build -t multilingual-parser:latest .
```

Build image with **full hybrid OCR deps** (installs EasyOCR + Google Vision client):

```bash
docker build --build-arg INSTALL_FULL_OCR=1 -t multilingual-parser:full .
```

Show CLI help:

```bash
docker run --rm multilingual-parser:latest python -m app.cli --help
```

Run parser with the repo sample (writes to `output/sample/`):

```bash
docker run --rm \
  -v "$(pwd):/app" -w /app \
  multilingual-parser:latest \
  python -m app.cli \
    --input /app/sample/sample.pdf \
    --out /app/output/sample
```

Run parser (auto-detect OCR) with a host PDF:

```bash
docker run --rm \
  -v "$(pwd):/app" -w /app \
  -v "$(cd "$(dirname "/path/to/book.pdf")" && pwd):/input" \
  multilingual-parser:latest \
  python -m app.cli \
    --input "/input/$(basename "/path/to/book.pdf")" \
    --out /app/out
```

Force OCR in Docker:

```bash
docker run --rm \
  -v "$(pwd):/app" -w /app \
  -v "$(cd "$(dirname "/path/to/book.pdf")" && pwd):/input" \
  multilingual-parser:latest \
  python -m app.cli \
    --input "/input/$(basename "/path/to/book.pdf")" \
    --out /app/out \
    --use-ocr
```

Force no-OCR in Docker:

```bash
docker run --rm \
  -v "$(pwd):/app" -w /app \
  -v "$(cd "$(dirname "/path/to/book.pdf")" && pwd):/input" \
  multilingual-parser:latest \
  python -m app.cli \
    --input "/input/$(basename "/path/to/book.pdf")" \
    --out /app/out \
    --no-use-ocr
```

Run tests inside Docker:

```bash
docker run --rm -v "$(pwd):/app" -w /app multilingual-parser:latest python -m pytest
```

### Google Cloud Vision (optional)
To enable the Google Vision OCR engine:
- Create a GCP service account with Vision API access
- Download a JSON key
- Set `GOOGLE_APPLICATION_CREDENTIALS` to that file

Local:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/service_account.json"
python -m app.cli --input path/to/book.pdf --out out --use-ocr
```

Docker (mount credentials read-only):

```bash
docker run --rm \
  -v "$(pwd):/app" -w /app \
  -v "/absolute/path/to/service_account.json:/secrets/gcp.json:ro" \
  -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/gcp.json \
  multilingual-parser:latest \
  python -m app.cli \
    --input /app/input/sample.pdf \
    --out /app/out/sample \
    --use-ocr
```

Or via `docker compose`:

```bash
docker compose run --rm test
```

---

### Repo map
- `docs/`: product + architecture plan
- `context/`: principles, policies, domain model
- `schemas/`: canonical JSON schema(s) for outputs
- `configs/`: YAML configuration for parser/OCR/export
- `app/`: implementation modules (pipeline, OCR, layout, tables, exporters)
- `scripts/`: helper scripts (`run_plan.sh`, `run_parse.sh`)

