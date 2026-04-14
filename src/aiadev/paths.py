"""Path resolution helpers.

During v0.2 the CLI assumes it runs from a working tree that contains the
framework (either the repository itself or a consumer project that cloned
it). The heuristic walks up from the current working directory looking for
a ``constitution.md`` at the root, falling back to the git toplevel.

Resource assets shipped in the wheel (phase 5.1, not yet) will override
this; until then every call resolves real on-disk files.
"""
from __future__ import annotations

import os
import pathlib
import subprocess


class FrameworkNotFound(RuntimeError):
    """Raised when ``aiadev`` cannot locate the framework root."""


def find_framework_root(start: pathlib.Path | None = None) -> pathlib.Path:
    """Return the directory containing ``constitution.md`` and ``templates/``.

    Walks up from ``start`` (default: cwd). Raises ``FrameworkNotFound``
    if no ancestor qualifies.
    """
    here = (start or pathlib.Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "constitution.md").is_file() and (candidate / "templates").is_dir():
            return candidate
    # Fallback: git toplevel, in case the user runs aiadev from a deep
    # subdirectory that predates the constitution.md landing.
    try:
        toplevel = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(here),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise FrameworkNotFound(
            "could not find constitution.md and templates/ in any parent of "
            f"{here}"
        )
    top = pathlib.Path(toplevel)
    if (top / "constitution.md").is_file() and (top / "templates").is_dir():
        return top
    raise FrameworkNotFound(
        f"git toplevel {top} does not contain constitution.md + templates/"
    )


def templates_dir(root: pathlib.Path | None = None) -> pathlib.Path:
    base = root or find_framework_root()
    return base / "templates"


def schemas_dir(root: pathlib.Path | None = None) -> pathlib.Path:
    base = root or find_framework_root()
    return base / "schemas"


def presets_dir(root: pathlib.Path | None = None) -> pathlib.Path:
    base = root or find_framework_root()
    return base / "presets"


def skill_frontmatter_schema(root: pathlib.Path | None = None) -> pathlib.Path:
    return schemas_dir(root) / "skill-frontmatter.schema.json"


def running_inside_framework_repo() -> bool:
    """True when cwd is inside the framework's own checkout, not a consumer."""
    try:
        root = find_framework_root()
    except FrameworkNotFound:
        return False
    return (root / "skills" / "implement" / "SKILL.md").is_file() and (root / "VERSION").is_file() and (root / "pyproject.toml").is_file() and root == pathlib.Path(os.path.abspath(root))
