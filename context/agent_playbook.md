## Agent playbook (operator workflow)

### When confidence is low
- Inspect `out/artifacts/page_XXXX_pre.png` for blur/skew/noise
- Re-run with higher DPI (e.g. 350–450)
- If low-confidence is localized, review `blocks[].spans[].confidence`

### Typical QA loop
- Parse → review HTML output (confidence badges)
- Export low-confidence blocks to a review queue (phase 2)
- Re-run after adjusting preprocessing parameters (phase 2 config tuning)

