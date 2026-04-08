## Deployment

### Local
- Install system deps (Poppler + Tesseract + Bengali model)
- Install python deps (`pip install -r requirements.txt`)
- Run CLI

### Docker
- Use a container image with:
  - Tesseract + `ben` traineddata
  - Python + dependencies
  - Poppler tools if needed for alternate rendering

### Kubernetes
- Run as a batch Job per PDF or as a worker Deployment consuming a queue.
- Set resource limits; OCR is CPU-heavy and EasyOCR may be GPU-heavy.

