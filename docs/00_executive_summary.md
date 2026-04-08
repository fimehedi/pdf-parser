## Executive summary

This project builds a **scanned PDF processing engine** for Bengali+English textbooks and study books. The engine ingests scanned PDFs (image pages), preprocesses them, runs OCR, detects layout and tables, and emits a canonical structured representation with **confidence scores**.

### Expected outcomes
- Reliable extraction of text blocks with reading order for multi-column pages
- Table regions exported to CSV when detected
- Structured outputs: JSON (canonical), Markdown (human-readable), HTML (renderable)
- Confidence scoring at OCR/layout/tables/images/semantic stages to support review workflows

