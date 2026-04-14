"""AI-Augmented Developer CLI package."""
from __future__ import annotations

import pathlib

_VERSION_FILE = pathlib.Path(__file__).resolve().parents[2] / "VERSION"

try:
    __version__ = _VERSION_FILE.read_text(encoding="utf-8").strip()
except FileNotFoundError:  # installed wheel resolves version at build time
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
