# Scanned textbook PDF engine (Bengali + English)

PDF processing for textbooks and question banks: **Bengali + English** mixed pages, multi-column layouts, **tables**, and **MCQ-style question extraction** (stem, options ক/খ/গ/ঘ or A–D, answer keys when present).

The engine can:

- Use **native text** on real PDFs (selectable text) with `pdfplumber` tables.
- Use **OCR** on scanned PDFs: **Tesseract 5** (`ben`+`eng`) + **EasyOCR** (`bn`+`en`), optionally **Google Cloud Vision**.

---

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**System:** Python **3.10+** (3.11+ recommended), **Tesseract** with **Bengali (`ben`)** and **English (`eng`)** trained data.

### macOS (Homebrew)

```bash
brew install tesseract tesseract-lang
tesseract --list-langs | egrep 'ben|eng'
```

### Windows

There is no `tesseract-lang` package name on Windows like Homebrew; you install **Tesseract** and ensure **`ben`** and **`eng`** `.traineddata` files are present (installer options or manual download).

**Option A — winget (recommended if available)**

```powershell
winget install --id UB-Mannheim.TesseractOCR
```

Use the installer UI to include **additional language data**, or place `ben.traineddata` / `eng.traineddata` under your Tesseract `tessdata` folder (often `C:\Program Files\Tesseract-OCR\tessdata`).

**Option B — Chocolatey**

```powershell
choco install tesseract
```

If `ben`/`eng` are missing, download traineddata files from the [tessdata](https://github.com/tesseract-ocr/tessdata) or [tessdata_best](https://github.com/tesseract-ocr/tessdata_best) repository into that `tessdata` directory.

**Option C — Scoop**

```powershell
scoop install tesseract
```

**Verify languages (PowerShell or Command Prompt)**

```powershell
tesseract --list-langs
tesseract --list-langs | findstr /i "ben eng"
```

**PATH:** Ensure the folder containing `tesseract.exe` is on your `PATH` (installer usually offers this). Restart the terminal after installing.

**Run the CLI on Windows**

```powershell
.\.venv\Scripts\activate
python -m app.cli --input C:\path\to\book.pdf --out out
```

```bash
# Typical CLI (macOS / Linux / Git Bash on Windows)
python -m app.cli --input path/to/book.pdf --out out
```

**Full-quality Bangla OCR profile** (see [Full mode vs normal mode](#full-mode-vs-normal-mode)):

```bash
python -m app.cli --input path/to/book.pdf --out out --use-ocr \
  --ocr-config configs/ocr_config.full.yaml --dpi 350
```

```powershell
# Windows (PowerShell): line continuation is the backtick `
python -m app.cli --input C:\path\to\book.pdf --out out --use-ocr `
  --ocr-config configs/ocr_config.full.yaml --dpi 350
```

---

## CLI reference

There is **no subcommand** — pass options directly to `python -m app.cli`.

| Option | Short | Default | Description |
|--------|--------|---------|-------------|
| `--input` | `-i` | *(required)* | Path to input `.pdf` |
| `--out` | `-o` | `out` | Output directory |
| `--dpi` | | `300` | Render DPI for OCR (higher often helps small Bangla text; try **300–400**) |
| `--config` | | `configs/parser_config.yaml` | Parser YAML (`processing.use_ocr`, `pdf.dpi`, …) if file exists |
| `--ocr-config` | | `configs/ocr_config.yaml` | OCR/hybrid YAML (`ocr.engines`, thresholds, GPU, preprocess profile, …) if file exists |
| `--use-ocr` | | | Force OCR path |
| `--no-use-ocr` | | | Force native text path (no OCR) |

**Help:**

```bash
python -m app.cli --help
```

**Logging:** set `LOG_LEVEL` (e.g. `DEBUG`, `INFO`).

---

## OCR on or off (`use_ocr`)

| Situation | Command / config |
|-----------|-------------------|
| **Auto** (default) | Omit both flags. If most pages have enough selectable text → native path; else OCR. |
| **Force OCR** (scans, or you want images/artifacts) | `--use-ocr` |
| **Force native text** (real PDF, no OCR) | `--no-use-ocr` |
| **From parser config** | `configs/parser_config.yaml` → `processing.use_ocr`: `null` / `true` / `false` |

CLI flags override the parser config when you pass `--use-ocr` / `--no-use-ocr`.

---

## Full mode vs normal mode

These are **not** separate CLI switches — they are **OCR configuration profiles** selected with `--ocr-config`.

### Normal mode — `configs/ocr_config.yaml` (default)

- **Engines:** `google_vision`, `tesseract`, `easyocr` (each runs if dependencies/credentials allow).
- **Auto-approve threshold:** **0.85** (blocks below → `review_tasks.json`).
- **EasyOCR GPU:** **off** by default (`easyocr.gpu: false`).
- **Preprocess:** `preprocess.profile: default`.
- **Consensus / weights:** enabled with moderate defaults (two engines can boost score when they agree).

**Typical command:**

```bash
python -m app.cli --input book.pdf --out out --use-ocr \
  --ocr-config configs/ocr_config.yaml
```

(Omit `--ocr-config` if the default path is fine.)

### Full mode — `configs/ocr_config.full.yaml`

Aimed at **high-quality Bangla scans** (question banks, dense text):

- **Engines:** **Tesseract + EasyOCR only** (no Google in the list — add it in a copy of the file if needed).
- **Threshold:** **0.90** (stricter auto-approve; tune to your QA needs).
- **Consensus:** stronger boost when two engines agree (`consensus_boost_delta: 0.10`).
- **EasyOCR:** **`gpu: true`** + tuned `readtext` (e.g. `mag_ratio`, thresholds).
- **Preprocess:** `bangla_scan` (stronger denoise / threshold tuning for Indic text).
- **Engine weights:** slightly favor EasyOCR for Bangla-heavy lines.

**Typical command:**

```bash
python -m app.cli --input book.pdf --out out --use-ocr \
  --ocr-config configs/ocr_config.full.yaml --dpi 350
```

You can **duplicate** `ocr_config.full.yaml`, edit engines/threshold/GPU, and point `--ocr-config` at your file.

---

## GPU (EasyOCR)

EasyOCR uses **PyTorch**. GPU acceleration applies when:

1. **`easyocr.gpu: true`** in the active OCR YAML (`configs/ocr_config.full.yaml` sets this).
2. A **CUDA-capable NVIDIA GPU** is installed with a **PyTorch build that matches your CUDA** (common on Linux/Windows workstations).
3. Dependencies are installed from **`requirements.txt`** (includes `easyocr` and pulls PyTorch as a dependency).

**CPU-only:** set `easyocr.gpu: false` in your OCR config (as in normal `ocr_config.yaml`). Parsing still works; EasyOCR is slower.

**Apple Silicon (M1/M2/M3):** EasyOCR/PyTorch may run on **MPS** depending on your PyTorch build; GPU flags in YAML still map to `Reader(..., gpu=True)`. If GPU init fails, use **`gpu: false`** or install a PyTorch build with MPS support and test in a small script.

**Docker default image** uses **`requirements-base.txt`** (no EasyOCR/Torch). For EasyOCR inside Docker, build with **`INSTALL_FULL_OCR=1`** (see [Docker](#docker)); **NVIDIA Container Toolkit** is required on the host to pass a GPU into the container.

**Checklist for NVIDIA + CUDA (Linux example):**

- NVIDIA driver + CUDA runtime compatible with your PyTorch wheel.
- In OCR YAML: `easyocr.gpu: true`.
- Optional: increase `--dpi` (e.g. **350–400**) for small Bangla text on scans.

---

## OCR configuration keys (YAML)

File: **`--ocr-config`** path (default `configs/ocr_config.yaml`).

| Section | Purpose |
|---------|---------|
| `ocr.engines` | List: `google_vision`, `tesseract`, `easyocr` |
| `ocr.confidence_threshold` | Block auto-approve cutoff (e.g. **0.85** normal, **0.90** full) |
| `ocr.consensus_boost` | When two top engines agree on text, raise confidence (toward 0.9+) |
| `ocr.consensus_min_similarity` | Minimum string similarity (0–1) to treat as “agreement” |
| `ocr.consensus_boost_delta` | How much to add to confidence on agreement (capped) |
| `ocr.bangla_easyocr_weight_bonus` | Extra score weight for EasyOCR when Bengali script dominates |
| `ocr.engine_weights` | Per-engine multipliers (`easyocr`, `tesseract`, `google_vision`) |
| `languages.tesseract` | e.g. `["ben", "eng"]` → combined `ben+eng` |
| `languages.easyocr` | e.g. `["bn", "en"]` |
| `tesseract.psm` / `oem` / `config_extra` | Tesseract page/legacy modes |
| `easyocr.gpu` | `true` / `false` |
| `easyocr.readtext` | Passed to `readtext(...)` (e.g. `mag_ratio`, `text_threshold`, `batch_size`) |
| `preprocess.profile` | `default` or `bangla_scan` |
| `semantic.extract_question_bank` | `true` / `false` — MCQ extraction + `question_bank.json` |

Parser-only file: **`--config`** → `configs/parser_config.yaml` (e.g. `processing.use_ocr`, `pdf.dpi`).

---

## Outputs (`--out`)

| Path | Description |
|------|-------------|
| `document.json` | Canonical document (pages, blocks, tables, **question_bank**, confidence) |
| `document.md` | Reading-order Markdown |
| `document.html` | HTML with confidence badges |
| `question_bank.json` | Extracted MCQ-style items (if `semantic.extract_question_bank` is true) |
| `tables/*.csv` | Tables (native or image-grid OCR) |
| `review_tasks.json` | Low-confidence OCR blocks (OCR path) |
| `artifacts/*.png` | Rendered + preprocessed pages (OCR path) |

---

## Google Cloud Vision (optional)

Add `google_vision` to `ocr.engines` and configure Application Default Credentials:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/service_account.json"
python -m app.cli --input book.pdf --out out --use-ocr
```

---

## Docker

**Light image** (Tesseract; no EasyOCR/Torch by default):

```bash
docker build -t multilingual-parser:latest .
```

**Full OCR dependencies** (EasyOCR + Google Vision client libraries):

```bash
docker build --build-arg INSTALL_FULL_OCR=1 -t multilingual-parser:full .
```

**CLI help:**

```bash
docker run --rm multilingual-parser:latest python -m app.cli --help
```

**Example run** (mount project and PDF; **no** `parse` subcommand):

```bash
docker run --rm \
  -v "$(pwd):/app" -w /app \
  -v "/path/to/pdf_dir:/input:ro" \
  multilingual-parser:full \
  python -m app.cli \
    --input "/input/your.pdf" \
    --out /app/out \
    --use-ocr \
    --ocr-config /app/configs/ocr_config.full.yaml
```

**GPU in Docker:** use NVIDIA runtime (`--gpus all`) and a CUDA-capable **full** image; verify PyTorch/CUDA inside the image for your hardware.

See **[Testing through Docker](#testing-through-docker)** below for `docker compose` / `pytest` commands.

---

## Testing through Docker

The image already includes **Tesseract** (`ben` + `eng`) and system libraries; Python deps come from **`requirements-base.txt`** by default (lighter, **no EasyOCR/Torch**). Unit tests (`pytest`) run against your **mounted** project tree.

### 1. Build and run tests (default / slim image)

From the repo root:

```bash
docker compose build test
docker compose run --rm test
```

Or:

```bash
make docker-compose-test
```

You should see **`4 passed`** (or current test count).

### 2. Full OCR stack in the image (EasyOCR + PyTorch)

Match a local “full” install:

```bash
INSTALL_FULL_OCR=1 docker compose build test
INSTALL_FULL_OCR=1 docker compose run --rm test
```

Or:

```bash
make docker-build-full
docker run --rm -v "$(pwd):/app" -w /app multilingual-parser:full python -m pytest tests/ -v
```

### 3. Parse a PDF inside Docker

Mount the project so paths like `input/…` and `out/` work on the host:

```bash
docker compose build parser   # or: docker build -t multilingual-parser:latest .
docker run --rm \
  -v "$(pwd):/app" -w /app \
  multilingual-parser:latest \
  python -m app.cli \
    --input /app/input/bangla-sahitto.pdf \
    --out /app/out \
    --use-ocr
```

Outputs appear under **`./out`** on your machine.

For **full** OCR in the container (EasyOCR), build with `INSTALL_FULL_OCR=1` and use that image tag instead of `latest` if you built `multilingual-parser:full`.

**Note:** The default **`.dockerignore`** excludes `input/*.pdf` from the **build context** only; bind-mounting `./` still exposes your `input/` folder at runtime.

---

## Troubleshooting

### `TesseractNotFoundError` / `No such file or directory: 'tesseract'`

Install Tesseract on the host (see [macOS](#macos-homebrew) / [Windows](#windows)). Ensure the directory containing `tesseract` is on your **`PATH`** (open a **new** terminal after installing).

Check:

```bash
which tesseract
tesseract --version
```

If `tesseract` is installed but not found (e.g. GUI apps or IDEs with a minimal `PATH`), set the binary explicitly:

```bash
export TESSERACT_CMD="/opt/homebrew/bin/tesseract"   # Apple Silicon Homebrew
# export TESSERACT_CMD="/usr/local/bin/tesseract"    # Intel Homebrew
```

The app reads **`TESSERACT_CMD`** (or **`TESSERACT_PATH`**) in `app/ocr/tesseract_engine.py`.

### NumPy / PyTorch / EasyOCR warnings (`_ARRAY_API`, “compiled using NumPy 1.x”)

The project pins **`numpy<2`** in `requirements.txt` so PyTorch and EasyOCR work reliably. After changing requirements, reinstall:

```bash
pip install -r requirements.txt
```

---

## Repo layout

- `app/` — pipeline, OCR, layout, tables, exporters, MCQ extraction
- `configs/` — `parser_config.yaml`, `ocr_config.yaml`, `ocr_config.full.yaml`
- `schemas/` — JSON Schema for canonical output
- `docs/` — deeper design notes
- `context/` — product constraints and policies

---

## License

See `pyproject.toml` (proprietary unless changed).
