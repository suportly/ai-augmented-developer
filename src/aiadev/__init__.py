"""AI-Augmented Developer CLI package."""
from __future__ import annotations

import pathlib
from importlib.metadata import PackageNotFoundError, version as _pkg_version

# Resolution order:
#   1. importlib.metadata (works for installed wheels and editable installs).
#   2. The repo's VERSION file (works for in-repo execution before install).
try:
    __version__ = _pkg_version("aiadev")
except PackageNotFoundError:
    _VERSION_FILE = pathlib.Path(__file__).resolve().parents[2] / "VERSION"
    try:
        __version__ = _VERSION_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
