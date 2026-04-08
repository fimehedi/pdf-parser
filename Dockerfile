FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-ben \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ARG INSTALL_FULL_OCR=0

COPY requirements-base.txt /app/requirements-base.txt
COPY requirements.txt /app/requirements.txt

# Default: lightweight deps (no EasyOCR/Torch).
# Optional: full OCR deps (EasyOCR + Google Vision client).
RUN if [ "$INSTALL_FULL_OCR" = "1" ]; then \
      pip install --no-cache-dir -r requirements.txt ; \
    else \
      pip install --no-cache-dir -r requirements-base.txt ; \
    fi

COPY . /app

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "-m", "app.cli"]

