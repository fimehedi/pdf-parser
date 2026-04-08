# PDF parser (Bengali + English)

Turn textbook and question-bank PDFs into structured text: **blocks**, **tables** (CSV), **MCQ-style items** (JSON), and **HTML/Markdown** for review. Works on **text-based PDFs** (native text) and **scanned PDFs** (OCR).

---

## Prerequisites (what you need)

| Requirement | Required? | Notes |
|---------------|------------|--------|
| **Python 3.10+** | Yes (local) | 3.11+ recommended. Not needed if you only use Docker. |
| **Tesseract OCR** + **ben** + **eng** data | Yes (local) | Pre-installed in our Docker image. |
| **This repo + dependencies** | Yes | `pip install -r requirements.txt` locally, or use Docker. |
| **EasyOCR / PyTorch** | Optional | For hybrid OCR. Included in `requirements.txt`. Docker: use **`INSTALL_FULL_OCR=1`** when building. |
| **Google Cloud Vision** | Optional | Enable Vision API + service account JSON. See [Google Cloud Vision](#google-cloud-vision-optional). |

**Included Python libraries (see `requirements.txt`):** PyMuPDF, OpenCV, Tesseract bindings, EasyOCR, pdfplumber, Pydantic, Typer, etc.

---

## Two ways to run: local or Docker

| | **Local (your machine)** | **Docker** |
|---|--------------------------|------------|
| **Best for** | Daily development, GPU on your GPU setup, editing configs | Clean, repeatable runs; no local Python/Tesseract install |
| **Tesseract** | You install it (macOS/Windows/Linux) | Included in the image |
| **EasyOCR** | From `pip install -r requirements.txt` | Use a **full** image: `INSTALL_FULL_OCR=1` |
| **Important** | Run CLI from project folder; paths are relative to that folder | Always **mount the project**: `-v "$(pwd):/app" -w /app` so `input/` and `out/` exist inside the container |

---

## Local setup

### 1. Python environment

```bash
cd pdf-parser
python3 -m venv .venv
```

**Activate:**

- macOS / Linux: `source .venv/bin/activate`
- Windows (PowerShell): `.\.venv\Scripts\activate`

### 2. Install Python packages

```bash
pip install -r requirements.txt
```

### 3. Install Tesseract (system)

OCR needs **Tesseract** with **Bengali (`ben`)** and **English (`eng`)** language data.

**macOS (Homebrew)**

```bash
brew install tesseract tesseract-lang
tesseract --list-langs | egrep 'ben|eng'
```

**Windows**

- Install via [winget](https://winget.run/) (e.g. `UB-Mannheim.TesseractOCR`), [Chocolatey](https://chocolatey.org/), or [Scoop](https://scoop.sh/).
- Ensure **`ben`** and **`eng`** appear in `tesseract --list-langs` (add [tessdata](https://github.com/tesseract-ocr/tessdata) files if needed).
- Put `tesseract.exe` on your **PATH** (restart the terminal after install).

```powershell
tesseract --list-langs | findstr /i "ben eng"
```

**Linux (Debian/Ubuntu example)**

```bash
sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-ben tesseract-ocr-eng
tesseract --list-langs | grep -E 'ben|eng'
```

If Tesseract is installed but not found, set (example for Apple Silicon Homebrew):

```bash
export TESSERACT_CMD="/opt/homebrew/bin/tesseract"
```

### 4. Optional: environment file

Copy `.env.example` to `.env` and adjust (e.g. `GOOGLE_APPLICATION_CREDENTIALS` for Vision API).

### 5. Run on a PDF

Put a PDF in your project (e.g. `input/mybook.pdf`) and run:

```bash
python -m app.cli --input input/mybook.pdf --out out --use-ocr
```

- **`--use-ocr`** — use the OCR pipeline (needed for scans).
- Omit **`--use-ocr`** to let the tool **auto-detect** (text PDF vs scan), or use **`--no-use-ocr`** for text-only extraction.

**Windows path example:**

```powershell
python -m app.cli --input C:\path\to\pdf-parser\input\mybook.pdf --out out --use-ocr
```

---

## Docker setup

Images install **Tesseract** and OS libraries for you. Python deps come from **`requirements-base.txt`** by default (**lighter**, no EasyOCR/Torch). For **EasyOCR** + Google client libraries, build with **`INSTALL_FULL_OCR=1`**.

### Build

```bash
# Default (Tesseract + base Python deps)
docker build -t multilingual-parser:latest .

# Full OCR stack (EasyOCR, PyTorch, google-cloud-vision from requirements.txt)
docker build --build-arg INSTALL_FULL_OCR=1 -t multilingual-parser:full .
```

### Run (always mount the project)

Without **`-v "$(pwd):/app"`**, paths like `input/book.pdf` **do not exist** in the container.

```bash
docker run --rm \
  -v "$(pwd):/app" \
  -w /app \
  multilingual-parser:latest \
  python -m app.cli \
    --input /app/input/mybook.pdf \
    --out /app/out \
    --use-ocr
```

Results appear in **`./out`** on your host.

**Full OCR image** (replace tag if you built `:full`):

```bash
docker run --rm -v "$(pwd):/app" -w /app multilingual-parser:full \
  python -m app.cli --input /app/input/mybook.pdf --out /app/out --use-ocr \
  --ocr-config /app/configs/ocr_config.full.yaml --dpi 350
```

**Google Cloud Vision in Docker:** mount the JSON key and set the env var:

```bash
docker run --rm \
  -v "$(pwd):/app" -w /app \
  -v "/path/on/host/service-account.json:/secrets/gcp.json:ro" \
  -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/gcp.json \
  multilingual-parser:full \
  python -m app.cli --input /app/input/mybook.pdf --out /app/out --use-ocr \
  --ocr-config /app/configs/ocr_config.google_vision.yaml
```

**GPU (Linux + NVIDIA):** add `--gpus all` and use a CUDA-capable setup. **Docker Desktop on Mac** does not expose an NVIDIA GPU the same way.

### Tests in Docker

```bash
docker compose build test
docker compose run --rm test
```

Or: `make docker-compose-test` (same idea).

Full deps for tests that need EasyOCR:

```bash
INSTALL_FULL_OCR=1 docker compose build test
INSTALL_FULL_OCR=1 docker compose run --rm test
```

---

## CLI options (reference)

There is **no subcommand** — options go directly on `python -m app.cli`.

| Option | Short | Default | Description |
|--------|--------|---------|-------------|
| `--input` | `-i` | *(required)* | Path to the PDF |
| `--out` | `-o` | `out` | Output folder |
| `--dpi` | | `300` | Render DPI for OCR (try **300–400** for small Bangla text) |
| `--config` | | `configs/parser_config.yaml` | Parser settings (if file exists) |
| `--ocr-config` | | `configs/ocr_config.yaml` | OCR / hybrid engine settings (if file exists) |
| `--use-ocr` | | | Force OCR |
| `--no-use-ocr` | | | Force native text only |

```bash
python -m app.cli --help
```

Set **`LOG_LEVEL=DEBUG`** (or `INFO`) for more logs.

---

## OCR modes and config files

**How it works:** For each text region, the pipeline runs the engines listed under **`ocr.engines`** in your **`--ocr-config`** file, then **keeps the best-scoring result** (hybrid). Smaller presets only change which engines participate.

**Auto-detect OCR on/off:** omit `--use-ocr` — if most pages have selectable text, native extraction is used; otherwise OCR.

### Presets: Tesseract only / + EasyOCR / + Google Vision

| What you want | Preset file | You need installed |
|---------------|-------------|----------------------|
| **Tesseract only** | `configs/ocr_preset_tesseract_only.yaml` | Tesseract (`ben`+`eng`). Docker: default image is enough. |
| **Tesseract + EasyOCR** | `configs/ocr_preset_tesseract_easyocr.yaml` | Tesseract + EasyOCR (full `requirements.txt`). Docker: **`INSTALL_FULL_OCR=1`** image. |
| **Tesseract + EasyOCR + Google Vision** | `configs/ocr_preset_tesseract_easyocr_gcv.yaml` | All of the above + Vision API credentials in **`.env`**. Docker: **`multilingual-parser:full`** + mount credentials. |

Replace `input/mybook.pdf` and `out/run1` with your paths.

**Local (same pattern for all three — only `--ocr-config` changes):**

```bash
# 1) Tesseract only
python -m app.cli --input input/mybook.pdf --out out/run1 --use-ocr \
  --ocr-config configs/ocr_preset_tesseract_only.yaml

# 2) Tesseract + EasyOCR
python -m app.cli --input input/mybook.pdf --out out/run1 --use-ocr \
  --ocr-config configs/ocr_preset_tesseract_easyocr.yaml

# 3) Tesseract + EasyOCR + Google Vision (set GOOGLE_APPLICATION_CREDENTIALS first)
python -m app.cli --input input/mybook.pdf --out out/run1 --use-ocr \
  --ocr-config configs/ocr_preset_tesseract_easyocr_gcv.yaml
```

**Docker** (project must be mounted; adjust image tag):

```bash
# 1) Tesseract only — default slim image
docker run --rm -v "$(pwd):/app" -w /app multilingual-parser:latest \
  python -m app.cli --input /app/input/mybook.pdf --out /app/out/run1 --use-ocr \
  --ocr-config /app/configs/ocr_preset_tesseract_only.yaml

# 2) + EasyOCR — full image
docker run --rm -v "$(pwd):/app" -w /app multilingual-parser:full \
  python -m app.cli --input /app/input/mybook.pdf --out /app/out/run1 --use-ocr \
  --ocr-config /app/configs/ocr_preset_tesseract_easyocr.yaml

# 3) + Google Vision — full image + JSON key
docker run --rm -v "$(pwd):/app" -w /app \
  -v "/ABSOLUTE/PATH/service-account.json:/secrets/gcp.json:ro" \
  -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/gcp.json \
  multilingual-parser:full \
  python -m app.cli --input /app/input/mybook.pdf --out /app/out/run1 --use-ocr \
  --ocr-config /app/configs/ocr_preset_tesseract_easyocr_gcv.yaml
```

### Other bundled profiles

| Profile | File | Notes |
|---------|------|--------|
| **Default hybrid** | `configs/ocr_config.yaml` | Vision + Tesseract + EasyOCR (if each is available) |
| **Full / Bangla scans** | `configs/ocr_config.full.yaml` | Higher threshold, `bangla_scan` preprocess; engine list is Tesseract + EasyOCR unless you edit it |
| **Vision-first** | `configs/ocr_config.google_vision.yaml` | Tuned for Cloud Vision |

Example (full Bangla profile):

```bash
python -m app.cli --input input/mybook.pdf --out out/run1 --use-ocr \
  --ocr-config configs/ocr_config.full.yaml --dpi 350
```

Edit any YAML to tune **`ocr.engines`**, **`easyocr.gpu`**, **`preprocess.profile`**, etc.

---

## GPU (EasyOCR, local)

Set **`easyocr.gpu: true`** in your OCR YAML (e.g. full profile). Requires **NVIDIA + CUDA** PyTorch on Linux/Windows. On **Mac**, GPU support is limited; use **`gpu: false`** if you see errors.

---

## Outputs (written to `--out`)

| File / folder | Contents |
|----------------|----------|
| `document.json` | Full structured document + confidence |
| `document.md` | Reading order, Markdown |
| `document.html` | Review UI with confidence badges |
| `question_bank.json` | Detected MCQ-style items (if enabled in OCR config) |
| `tables/*.csv` | Tables |
| `review_tasks.json` | Low-confidence OCR blocks (for human review) |
| `artifacts/*.png` | Page images (OCR path) |

---

## Google Cloud Vision (optional)

1. Enable **Cloud Vision API** on Google Cloud and create a **service account** + **JSON key**.
2. Copy `configs/google_vision_service_account.sample.json` → `configs/google_vision_service_account.json` and paste your real key (this file is gitignored).
3. Copy `.env.example` → `.env` and set **`GOOGLE_APPLICATION_CREDENTIALS`** (or export the variable in the shell).
4. Use a config that lists **`google_vision`** under **`ocr.engines`**, e.g. **`configs/ocr_config.google_vision.yaml`**.

```bash
python -m app.cli --input input/mybook.pdf --out out --use-ocr \
  --ocr-config configs/ocr_config.google_vision.yaml
```

---

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| **`TesseractNotFoundError`** | Install Tesseract; check **`which tesseract`**. Set **`TESSERACT_CMD`** to the full path. |
| **`Invalid value for '--input'`** | Use a real path. In Docker, mount the repo and use e.g. **`/app/input/file.pdf`**. |
| **NumPy / PyTorch warnings** | Project pins **`numpy<2`**. Run **`pip install -r requirements.txt`** again. |
| **Google Vision errors** | Check API enabled, billing if required, and **`GOOGLE_APPLICATION_CREDENTIALS`** points to a valid JSON file. |

---

## Repository layout

| Path | Purpose |
|------|---------|
| `app/` | CLI, pipeline, OCR engines, tables, exports |
| `configs/` | Parser + OCR YAML, including **`ocr_preset_tesseract_only.yaml`**, **`ocr_preset_tesseract_easyocr.yaml`**, **`ocr_preset_tesseract_easyocr_gcv.yaml`**, Vision sample JSON |
| `schemas/` | JSON schemas for outputs |
| `docs/` | Extra technical notes |
| `tests/` | Pytest suite |

---

## License

See `pyproject.toml`.
