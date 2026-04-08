## Domain model (canonical)

### Entities
- **Document**: one PDF input, produces one canonical output bundle.
- **Page**: rendered image for page \(i\), including preprocessing artifacts.
- **Block**: a reading-order unit (paragraph, heading, list item, etc.) with bbox + OCR spans.
- **Span**: OCR token/line with bbox + confidence.
- **Table**: detected table region with extracted cells + exported CSV.
- **Image/Figure**: non-text region (diagram/figure) optionally linked with a caption block.

### Relationships
- Document → Pages (1..N)
- Page → Blocks (0..M)
- Page → Tables (0..K)
- Page → Images (0..L)
- Image ↔ CaptionBlock (0..1)

### Canonical outputs
The canonical JSON model is defined in `schemas/canonical_document_schema.json` and mirrored by Pydantic models in `app/models.py`.

