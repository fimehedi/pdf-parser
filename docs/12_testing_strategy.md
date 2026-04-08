## Testing strategy

### Unit tests
- Preprocessing invariants (deskew returns same size, output dtype)
- Layout block detection returns stable ordering on synthetic pages
- Confidence scoring clamping and signal presence

### Integration tests
- Parse a small fixture PDF and assert:
  - outputs exist (JSON/MD/HTML)
  - JSON conforms to schema
  - tables CSV created when expected

### End-to-end tests
- Run on representative textbooks:
  - 1-column lesson pages
  - 2-column exercise pages
  - pages with grid tables
  - low-quality scans
Compare outputs with manual spot checks guided by confidence.

