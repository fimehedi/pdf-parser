from __future__ import annotations

from pathlib import Path

import typer
from dotenv import load_dotenv

from app.config import load_parser_config
from app.logging_config import configure_logging
from app.ocr.gcv_env import apply_credentials_to_environ
from app.pipeline import parse_pdf

def parse(
    input: Path = typer.Option(..., "--input", "-i", exists=True, dir_okay=False, help="Input PDF path"),
    out: Path = typer.Option(Path("out"), "--out", "-o", help="Output directory"),
    dpi: int = typer.Option(300, "--dpi", help="Render DPI for PDF pages"),
    config: Path = typer.Option(Path("configs/parser_config.yaml"), "--config", help="Path to parser YAML config"),
    ocr_config: Path = typer.Option(Path("configs/ocr_config.yaml"), "--ocr-config", help="Path to OCR YAML config"),
    use_ocr: bool | None = typer.Option(
        None,
        "--use-ocr/--no-use-ocr",
        help="When true, force OCR. When false, force native text extraction. If omitted, auto-detect (or config).",
    ),
    cmg: bool | None = typer.Option(
        None,
        "--cmg/--no-cmg",
        help="Alias for --use-ocr/--no-use-ocr (kept for backwards compatibility).",
        hidden=True,
    ),
):
    """Parse an educational PDF; OCR only when needed or when cmg=true."""
    load_dotenv()
    apply_credentials_to_environ()
    configure_logging()
    cfg = load_parser_config(config) if config.exists() else None
    effective_use_ocr = use_ocr if use_ocr is not None else (cmg if cmg is not None else (cfg.use_ocr if cfg else None))
    effective_dpi = dpi if dpi else (cfg.dpi if cfg else 300)
    parse_pdf(
        input_pdf=input,
        out_dir=out,
        dpi=effective_dpi,
        use_ocr=effective_use_ocr,
        ocr_config_path=ocr_config if ocr_config.exists() else None,
    )


def main() -> None:
    # Single-command CLI: options are passed directly (no subcommand).
    typer.run(parse)


if __name__ == "__main__":
    main()

