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
1. Install dependency: `google-cloud-vision`
2. Provide credentials with ADC:
   - Set `GOOGLE_APPLICATION_CREDENTIALS=/path/to/service_account.json`
3. Enable Vision API in your GCP project

