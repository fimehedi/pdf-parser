## Output schema

### Canonical JSON
- Schema: `schemas/canonical_document_schema.json`
- Key fields:
  - `pages[]`: rendered page metadata + artifact paths
  - `blocks[]`: OCR text blocks with bbox, reading order, spans, and confidence
  - `tables[]`: table bboxes with extracted cells and exported CSV paths
  - `images[]`: figure regions (v1 emits empty; reserved for phase 2)
  - `confidence`: stage and overall scores

### CSV tables
- Stored in `out/tables/`
- Each table referenced from `tables[].csv_path`

### Markdown and HTML
- Markdown: linearized reading-order text
- HTML: blocks rendered with confidence badges for fast review

