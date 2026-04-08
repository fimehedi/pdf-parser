## Hybrid OCR pipeline (Bangla-first)

### Objective
Improve Bengali OCR accuracy on scanned educational PDFs by combining multiple engines and selecting the best result per text block.

### Engines
- **Google Cloud Vision API** (`google_vision`)
  - Best overall OCR quality for Bangla in many real-world scans
  - Requires billing + credentials
- **Tesseract 5** (`tesseract`)
  - Free, strong for clean scans with `ben+eng`
- **EasyOCR** (`easyocr`)
  - Free, often good for mixed scripts; can use GPU if available

### Flow (per text block)
1. Preprocess (deskew + simple dewarp + binarize)
2. Detect block regions
3. Run OCR engines in parallel for each block
4. Merge by confidence:
   - Pick the highest-confidence candidate
   - Tie-breaker: longer text
5. Apply threshold:
   - If confidence \(\ge 0.85\) → auto-approve
   - Else → flag for human review

### Human review output
Low-confidence blocks are exported to `out/review_tasks.json`, including:
- block id + bbox
- chosen OCR text + confidence
- candidate previews for comparison

### Google Vision setup
1. Install dependency: `google-cloud-vision` (included in `requirements.txt`).
2. Enable **Cloud Vision API** on your GCP project; create a service account and download its JSON key.
3. Copy `configs/google_vision_service_account.sample.json` to `configs/google_vision_service_account.json`, fill in real values, and set `GOOGLE_APPLICATION_CREDENTIALS` in `.env` (see `.env.example`). The CLI calls `load_dotenv()` so the path can be relative to the working directory.
4. Keep `google_vision.enabled: true` in `configs/ocr_config.yaml` (or use `configs/ocr_config.google_vision.yaml`).

