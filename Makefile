.PHONY: docker-build docker-build-full docker-help docker-test docker-compose-test docker-parse

docker-build:
	docker build -t multilingual-parser:latest .

docker-build-full:
	docker build --build-arg INSTALL_FULL_OCR=1 -t multilingual-parser:full .

docker-help:
	docker run --rm multilingual-parser:latest python -m app.cli --help

docker-test:
	docker run --rm -v "$$(pwd):/app" -w /app multilingual-parser:latest python -m pytest tests/ -v

# Same as docker-test but uses docker-compose.yml (respects INSTALL_FULL_OCR=0|1 when building).
docker-compose-test:
	docker compose run --rm test

docker-parse:
	@if [ -z "$(PDF)" ]; then echo "Usage: make docker-parse PDF=/path/to/file.pdf OUT=out"; exit 2; fi
	@OUT_DIR=$${OUT:-out}; \
	docker run --rm \
	  -v "$$(pwd):/app" -w /app \
	  -v "$$(cd "$$(dirname "$(PDF)")" && pwd):/input" \
	  multilingual-parser:latest \
	  python -m app.cli --input "/input/$$(basename "$(PDF)")" --out "/app/$${OUT_DIR}" --dpi 300

