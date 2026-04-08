from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ParserConfig:
    raw: dict[str, Any]

    @property
    def output_dir(self) -> Path:
        return Path(self.raw.get("io", {}).get("output_dir", "out"))

    @property
    def artifacts_dir(self) -> Path:
        return Path(self.raw.get("io", {}).get("artifacts_dir", "artifacts"))

    @property
    def dpi(self) -> int:
        return int(self.raw.get("pdf", {}).get("dpi", 300))

    @property
    def use_ocr(self) -> bool | None:
        v = self.raw.get("processing", {}).get("use_ocr", None)
        if v is None:
            return None
        return bool(v)


def load_yaml(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {p}, got {type(data).__name__}")
    return data


def load_parser_config(path: str | Path) -> ParserConfig:
    return ParserConfig(raw=load_yaml(path))

