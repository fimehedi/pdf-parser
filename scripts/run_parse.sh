#!/usr/bin/env bash
set -euo pipefail

INPUT="${1:-}"
OUT="${2:-out}"

if [[ -z "${INPUT}" ]]; then
  echo "Usage: scripts/run_parse.sh <input.pdf> [out_dir]" >&2
  exit 2
fi

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 -m app.cli parse --input "${INPUT}" --out "${OUT}"
echo "Done. Outputs in: ${OUT}/"

