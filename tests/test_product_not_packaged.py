"""T015 — aiadev dogfoods its own product context, and it never ships.

Spec: specs/0023-product-context/spec.md, cl-5 and its success criterion:
the repository carries ``specs/_product/{mission,tech-stack,roadmap}.md``,
and none of those files reaches the sdist, the wheel, or a consumer install.
"""
from __future__ import annotations

import ast
import pathlib
import re

import pytest

from aiadev.framework_artifacts import iter_framework_artifacts

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PRODUCT_DIR = REPO_ROOT / "specs" / "_product"
SECTION_RE = re.compile(r"<!-- section: (.+?) -->")


@pytest.mark.parametrize("name", ["mission", "tech-stack", "roadmap"])
def test_repo_has_product_context(name: str) -> None:
    doc = PRODUCT_DIR / f"{name}.md"
    assert doc.is_file(), f"{doc.relative_to(REPO_ROOT)} is missing"
    template = REPO_ROOT / "templates" / f"{name}-template.md"
    expected = SECTION_RE.findall(template.read_text(encoding="utf-8"))
    actual = SECTION_RE.findall(doc.read_text(encoding="utf-8"))
    assert actual == expected, f"{doc.name} must keep the template's section anchors"


def test_manifest_in_does_not_ship_specs() -> None:
    manifest = (REPO_ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    assert not re.search(r"^\s*(recursive-)?include\s+specs\b", manifest, re.MULTILINE)


def test_sync_assets_does_not_bundle_specs() -> None:
    tree = ast.parse((REPO_ROOT / "scripts" / "sync_assets.py").read_text(encoding="utf-8"))
    sources = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    assert not any(s == "specs" or s.startswith("specs/") for s in sources)


def test_framework_artifacts_never_emit_specs() -> None:
    paths = [path for _role, _name, path in iter_framework_artifacts(REPO_ROOT)]
    assert paths, "sanity: the framework must emit some artifacts"
    assert not any("specs" in path.relative_to(REPO_ROOT).parts for path in paths)
