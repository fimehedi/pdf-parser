"""Resolve and validate Google Cloud Vision (Application Default) credentials paths."""

from __future__ import annotations

import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)


def resolve_credentials_file() -> Path | None:
    """
    Return absolute Path to the service account JSON if GOOGLE_APPLICATION_CREDENTIALS
    is set and the file exists; None otherwise.
    """
    raw = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if not raw:
        return None
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    else:
        p = p.resolve()
    return p if p.is_file() else None


def apply_credentials_to_environ() -> Path | None:
    """
    If credentials file exists, set GOOGLE_APPLICATION_CREDENTIALS to its absolute path.
    Call after load_dotenv() so relative paths from .env resolve from cwd.
    """
    p = resolve_credentials_file()
    if p is not None:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(p)
        return p
    return None


def warn_if_google_vision_unconfigured(engines: list[str]) -> None:
    if "google_vision" not in engines:
        return
    if resolve_credentials_file() is not None:
        return
    raw = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if not raw:
        log.warning(
            "OCR engine 'google_vision' is enabled but GOOGLE_APPLICATION_CREDENTIALS is not set. "
            "Copy configs/google_vision_service_account.sample.json to configs/google_vision_service_account.json "
            "(or use secrets/) and set the env var. See .env.example."
        )
    else:
        log.warning(
            "GOOGLE_APPLICATION_CREDENTIALS=%s does not point to an existing file; Google Vision will fail per block.",
            raw,
        )
