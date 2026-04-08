.PHONY: docker-build docker-help docker-test docker-parse

docker-build:
	docker build -t multilingual-parser:latest .

docker-help:
	docker run --rm multilingual-parser:latest python -m app.cli --help

docker-test:
	docker run --rm -v "$$(pwd):/app" -w /app multilingual-parser:latest python -m pytest

docker-parse:
	@if [ -z "$(PDF)" ]; then echo "Usage: make docker-parse PDF=/path/to/file.pdf OUT=out"; exit 2; fi
	@OUT_DIR=$${OUT:-out}; \
	docker run --rm \
	  -v "$$(pwd):/app" -w /app \
	  -v "$$(cd "$$(dirname "$(PDF)")" && pwd):/input" \
	  multilingual-parser:latest \
	  python -m app.cli parse --input "/input/$$(basename "$(PDF)")" --out "/app/$${OUT_DIR}" --dpi 300

