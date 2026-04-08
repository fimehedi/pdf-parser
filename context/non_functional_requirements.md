## Non-functional requirements

- **Reliability**: do not crash on malformed PDFs; emit partial outputs with lowered confidence.
- **Reproducibility**: export intermediate artifacts (rendered + preprocessed pages).
- **Observability**: structured logs and per-stage timing (to be extended).
- **Performance**: page-parallel processing (phase 2); baseline is single-process.
- **Portability**: support local runs and containerized deployment (Docker).
- **Security**: treat PDFs as untrusted; avoid executing embedded content.

