## Security

### Threat model
- PDFs are untrusted input files.
- Adversarial PDFs may attempt to trigger parser crashes or resource exhaustion.

### Controls (v1)
- Render using PyMuPDF (no JS execution).
- Avoid executing embedded actions/scripts.
- Write outputs only to the designated output folder.

### Recommended hardening (prod)
- Run in container with:
  - read-only input mount
  - resource limits (CPU/memory/timeouts)
  - non-root user
- Add per-page timeouts and max page limits.

