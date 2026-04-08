## Parsing principles

### 1) Scanned-first
Assume pages are images. Prefer image rendering + image preprocessing + OCR.

### 2) Preserve evidence
Store artifacts (rendered pages and preprocessed pages) so reviewers can reproduce issues.

### 3) Emit confidence everywhere
Confidence is not one number: it is stage-specific (OCR/layout/tables/images/semantic) and traceable via signals.

### 4) Keep a canonical intermediate representation (CIR)
All exports (JSON/CSV/Markdown/HTML) derive from a single CIR to ensure consistency.

### 5) Degrade gracefully
If tables/figures cannot be reliably extracted, fall back to text blocks and reduce confidence rather than failing.

