from __future__ import annotations

import json
from pathlib import Path

import jsonschema


def test_canonical_schema_is_valid() -> None:
    root = Path(__file__).resolve().parents[2]
    schemas = root / "schemas"
    doc = json.loads((schemas / "canonical_document_schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(doc)


def test_cli_imports() -> None:
    import app.cli  # noqa: F401

