"""Load project .env files into os.environ.

Uses python-dotenv when available; otherwise falls back to a tiny parser.
Real environment variables always win (existing os.environ entries are not
overwritten). .env files are gitignored and never shipped in git, so Cloud Run
env vars are untouched by this.
"""

from __future__ import annotations

import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATHS = (_PROJECT_ROOT / ".env", _PROJECT_ROOT / ".env.local")

_loaded = False


def _parse_env_file(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def load_project_env() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    try:
        from dotenv import load_dotenv

        for path in _ENV_PATHS:
            if path.exists():
                load_dotenv(path, override=False)
        return
    except Exception:
        pass
    for path in _ENV_PATHS:
        if path.exists():
            _parse_env_file(path)
