## Confidence scoring (v1)

### Goals
- Provide a **stage-specific** and **debuggable** confidence system.
- Drive review workflows: low-confidence pages/blocks are prioritized for human QA.

### Scoring layers
- **Span confidence**: per OCR token/line (engine-provided)
- **Block confidence**: aggregated from spans (per block)
- **Stage confidence**:
  - OCR: based on mean block confidence + low-confidence ratio + blur penalty
  - Layout: based on block count, column plausibility, overlap ratio
  - Tables: based on grid quality + inferred structure + OCR proxy
  - Images: based on detection count and caption-link rate (phase 2)
  - Semantic: heuristic in v1; upgraded in later phases
- **Overall confidence**: weighted combination of stage confidences

### Implemented formulas (current code)
- OCR stage: `app/confidence.py::confidence_from_ocr`
- Layout stage: `app/confidence.py::confidence_from_layout`
- Tables stage: `app/confidence.py::confidence_from_tables`
- Overall: `app/confidence.py::confidence_overall`

### Signals
All confidence objects include `signals` so that dashboards/debugging can show:
- mean/low ratios
- blur score and applied penalty
- overlap ratio
- table grid/structure scores

