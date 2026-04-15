"""Tests for :mod:`aiadev.project_introspect`."""
from __future__ import annotations

import json
import pathlib

from aiadev.project_introspect import (
    apply_stack_block,
    introspect,
    render_stack_block,
)


def _write(path: pathlib.Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class TestIntrospect:
    def test_empty_project_returns_empty_report(self, tmp_path: pathlib.Path) -> None:
        report = introspect(tmp_path)
        assert report.is_empty

    def test_detects_node_and_frameworks(self, tmp_path: pathlib.Path) -> None:
        _write(
            tmp_path / "package.json",
            json.dumps(
                {
                    "scripts": {"dev": "vite", "build": "vite build", "test": "vitest"},
                    "dependencies": {"react": "^18", "vite": "^5"},
                }
            ),
        )
        report = introspect(tmp_path)
        assert "JavaScript/TypeScript" in report.languages
        assert "React" in report.frameworks
        assert "Vite" in report.frameworks
        assert "npm run dev" in report.run_commands
        assert "npm run build" in report.run_commands

    def test_detects_typescript_when_tsconfig_present(
        self, tmp_path: pathlib.Path
    ) -> None:
        _write(tmp_path / "package.json", "{}")
        _write(tmp_path / "tsconfig.json", "{}")
        report = introspect(tmp_path)
        assert "TypeScript" in report.languages

    def test_detects_python_django_celery(self, tmp_path: pathlib.Path) -> None:
        _write(
            tmp_path / "pyproject.toml",
            '[project]\nname = "demo"\ndependencies = ["django>=5", "celery>=5"]\n',
        )
        _write(tmp_path / "manage.py", "# django entry")
        report = introspect(tmp_path)
        assert "Python" in report.languages
        assert "Django" in report.frameworks
        assert "Celery" in report.frameworks
        assert "python manage.py runserver" in report.run_commands

    def test_detects_rust_go_dart(self, tmp_path: pathlib.Path) -> None:
        _write(tmp_path / "Cargo.toml", "[package]\nname='c'")
        _write(tmp_path / "go.mod", "module demo\n")
        _write(
            tmp_path / "pubspec.yaml",
            "name: demo\ndependencies:\n  flutter:\n    sdk: flutter\n",
        )
        report = introspect(tmp_path)
        assert "Rust" in report.languages
        assert "Go" in report.languages
        assert "Dart" in report.languages
        assert "Flutter" in report.frameworks

    def test_detects_docker_services(self, tmp_path: pathlib.Path) -> None:
        _write(
            tmp_path / "docker-compose.yml",
            "services:\n  backend:\n    image: python:3.12\n  db:\n    image: postgres:15\n",
        )
        report = introspect(tmp_path)
        assert {"backend", "db"} <= set(report.services)

    def test_detects_makefile_targets(self, tmp_path: pathlib.Path) -> None:
        _write(
            tmp_path / "Makefile",
            "dev:\n\tpython app.py\n\ntest:\n\tpytest\n\n.PHONY: dev test\n",
        )
        report = introspect(tmp_path)
        assert {"dev", "test"} <= set(report.make_targets)

    def test_detects_github_workflows(self, tmp_path: pathlib.Path) -> None:
        _write(tmp_path / ".github" / "workflows" / "ci.yml", "name: CI\n")
        _write(tmp_path / ".github" / "workflows" / "release.yml", "name: Release\n")
        report = introspect(tmp_path)
        assert {"ci.yml", "release.yml"} <= set(report.ci_pipelines)

    def test_report_ordering_is_stable(self, tmp_path: pathlib.Path) -> None:
        _write(
            tmp_path / "package.json",
            json.dumps({"dependencies": {"vue": "^3", "react": "^18"}}),
        )
        first = introspect(tmp_path)
        second = introspect(tmp_path)
        assert first.frameworks == second.frameworks == ["React", "Vue"]


class TestRenderStackBlock:
    def test_empty_report_still_includes_timestamp(self) -> None:
        from aiadev.project_introspect import StackReport

        block = render_stack_block(StackReport(), "2026-04-15T18:00:00Z")
        assert "No recognised stack files found." in block
        assert "2026-04-15T18:00:00Z" in block

    def test_full_report_mentions_every_section(self) -> None:
        from aiadev.project_introspect import StackReport

        report = StackReport(
            languages=["Python"],
            frameworks=["Django"],
            run_commands=["make dev"],
            services=["api"],
            ci_pipelines=["ci.yml"],
            make_targets=["dev"],
        )
        block = render_stack_block(report, "2026-04-15T18:00:00Z")
        assert "Python" in block and "Django" in block
        assert "`make dev`" in block
        assert "api" in block
        assert "ci.yml" in block


class TestApplyStackBlock:
    def test_replaces_existing_block_verbatim(self) -> None:
        original = (
            "# Project\n\n"
            "<!-- aiadev:auto-stack:start -->\n"
            "old content\n"
            "<!-- aiadev:auto-stack:end -->\n\n"
            "## Manual notes\nKeep me.\n"
        )
        new_text, appended = apply_stack_block(original, "shiny new")
        assert not appended
        assert "old content" not in new_text
        assert "shiny new" in new_text
        # Preserved text outside the markers — byte-for-byte.
        assert "## Manual notes\nKeep me." in new_text

    def test_appends_when_markers_missing(self) -> None:
        original = "# Project\n\nJust notes.\n"
        new_text, appended = apply_stack_block(original, "detected stack")
        assert appended
        assert "<!-- aiadev:auto-stack:start -->" in new_text
        assert "detected stack" in new_text
        assert new_text.startswith(original.rstrip() + "\n\n<!-- aiadev")

    def test_preserves_multibyte_outside_markers(self) -> None:
        original = (
            "# Projeto — acentuação é OK 🚀\n\n"
            "<!-- aiadev:auto-stack:start -->\n"
            "old\n"
            "<!-- aiadev:auto-stack:end -->\n"
        )
        new_text, _ = apply_stack_block(original, "new block")
        assert "acentuação é OK 🚀" in new_text
