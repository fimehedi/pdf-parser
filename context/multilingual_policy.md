## Multilingual policy (Bengali + English)

### OCR language strategy
- Default OCR language set: **Bengali + English** simultaneously.
- For Tesseract: use `ben+eng` when available.
- Mixed-language lines are expected; avoid forcing single-language OCR per block unless signals strongly suggest it.

### Text normalization
- Preserve original Unicode as much as possible.
- Avoid aggressive punctuation normalization that can harm Bengali orthography.

### Mixed-language confidence
Confidence should be penalized when:
- OCR outputs show high symbol noise ratio
- Many low-confidence tokens cluster in a region
- Script-mix appears inconsistent with expected textbook style (signal, not hard rule)

