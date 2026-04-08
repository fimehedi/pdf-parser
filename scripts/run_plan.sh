#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 - <<'PY'
from pathlib import Path
import json
import jsonschema

root = Path(".")
schemas = root / "schemas"
doc = json.loads((schemas / "canonical_document_schema.json").read_text(encoding="utf-8"))
resolver = jsonschema.RefResolver(base_uri=schemas.as_uri() + "/", referrer=doc)
jsonschema.Draft202012Validator.check_schema(doc)
print("OK: canonical_document_schema.json is valid Draft 2020-12 schema")

# Sanity-check referenced defs by loading them
for name in ["blocks_schema.json", "table_schema.json"]:
    json.loads((schemas / name).read_text(encoding="utf-8"))
print("OK: referenced schemas load")
PY

echo "PLAN artifacts: schemas/configs present and valid."

