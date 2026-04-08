from __future__ import annotations

import csv
from pathlib import Path


def export_csv_matrix(matrix: list[list[str]], path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for row in matrix:
            writer.writerow(row)
    return p

