## Runbook

### Parse a PDF

```bash
./scripts/run_parse.sh path/to/book.pdf out/
```

### Inspect outputs
- `out/document.html`: quickest review (includes confidence badges)
- `out/document.json`: canonical structured output
- `out/tables/*.csv`: extracted tables (when detected)
- `out/artifacts/*.png`: rendered and preprocessed pages for debugging

### Common issues
- **Tesseract not found**: install system `tesseract` and Bengali language pack.
- **Low OCR confidence**: re-run with higher `--dpi` (e.g. 400) and review blur/skew artifacts.
- **No tables detected**: tables may lack grid lines; v1 detector is grid-based.

