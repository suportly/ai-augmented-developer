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


def _is_framework_root(candidate: pathlib.Path) -> bool:
    return (
        (candidate / "constitution.md").is_file()
        and (candidate / "templates").is_dir()
    )


def find_framework_root(start: pathlib.Path | None = None) -> pathlib.Path:
    """Return the directory containing ``constitution.md`` and ``templates/``.

    Resolution order:

    1. ``AIADEV_ROOT`` environment variable, when set and valid.
    2. Walk up from ``start`` (default: cwd).
    3. Git toplevel of ``start``, when inside a repo.
    4. The directory where the installed ``aiadev`` package lives — lets
       ``pip install -e .`` consumers run the CLI from anywhere.

    Raises :class:`FrameworkNotFound` if none of those qualify.
    """
    env_root = os.environ.get("AIADEV_ROOT")
    if env_root:
        candidate = pathlib.Path(env_root).expanduser().resolve()
        if _is_framework_root(candidate):
            return candidate
        # An explicit AIADEV_ROOT that does not satisfy the check is a
        # user mistake, not an invitation to keep looking.
        raise FrameworkNotFound(
            f"AIADEV_ROOT={candidate} does not contain constitution.md + templates/"
        )

    here = (start or pathlib.Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if _is_framework_root(candidate):
            return candidate

    try:
        toplevel = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(here),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        toplevel = ""
    if toplevel:
        top = pathlib.Path(toplevel)
        if _is_framework_root(top):
            return top

    # Package-location fallback: paths.py lives at src/aiadev/paths.py, so
    # parents[2] is the repo root when installed in editable mode.
    package_candidate = pathlib.Path(__file__).resolve().parents[2]
    if _is_framework_root(package_candidate):
        return package_candidate

    # Wheel install fallback: the assets bundled inside the package live
    # at ``aiadev/_assets/`` (populated by scripts/sync_assets.py before
    # the wheel is built). This is the path that lets ``pip install
    # aiadev`` work without a framework checkout on disk.
    bundled_assets = pathlib.Path(__file__).resolve().parent / "_assets"
    if _is_framework_root(bundled_assets):
        return bundled_assets

    raise FrameworkNotFound(
        "could not locate the aiadev framework root. Looked at AIADEV_ROOT, "
        f"every parent of {here}, the git toplevel, the package install "
        "location, and the wheel-bundled _assets/. None contained "
        "constitution.md + templates/."
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
