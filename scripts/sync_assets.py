#!/usr/bin/env python3
"""Copy the framework's runtime assets into ``src/aiadev/_assets/``.

`pip install aiadev` ships a wheel; the wheel must contain the
``constitution.md`` + ``templates/`` + ``schemas/`` + ``presets/``
trees because the runtime resolves them via
:func:`aiadev.paths.find_framework_root`'s package-bundled-assets
fallback.

This script copies them from the repo root into the package's
``_assets/`` directory before ``python -m build`` is invoked.

The copied tree is gitignored — only the source-of-truth at the repo
root is committed. Run this script before building (CI does it
automatically as part of the publish workflow).
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DEST = REPO_ROOT / "src" / "aiadev" / "_assets"

# (source-relative-to-repo-root, dest-name-under-_assets) pairs.
COPY_PLAN: list[tuple[str, str]] = [
    ("constitution.md", "constitution.md"),
    ("templates", "templates"),
    ("schemas", "schemas"),
    ("skills", "skills"),
    ("presets", "presets"),
    ("agents", "agents"),
]


def main() -> int:
    if ASSETS_DEST.exists():
        shutil.rmtree(ASSETS_DEST)
    ASSETS_DEST.mkdir(parents=True)

    for src_rel, dest_rel in COPY_PLAN:
        src = REPO_ROOT / src_rel
        dest = ASSETS_DEST / dest_rel
        if not src.exists():
            print(f"error: source missing: {src}", file=sys.stderr)
            return 1
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)
        print(f"synced {src_rel} -> {dest.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
