"""T014 — tool catalog derived from SKILL.md frontmatter."""
from __future__ import annotations

import pathlib


class TestListDefinitions:
    def test_returns_8_pipeline_skills(self, framework_root: pathlib.Path) -> None:
        from aiadev.tools._definitions import list_definitions

        defs = list_definitions(framework_root)
        names = {d["name"] for d in defs}
        assert names == {
            "specify", "clarify", "plan", "tasks",
            "implement", "analyze", "checklist", "constitution",
        }

    def test_each_has_description_and_input_schema(
        self, framework_root: pathlib.Path
    ) -> None:
        from aiadev.tools._definitions import list_definitions

        for d in list_definitions(framework_root):
            assert "description" in d and len(d["description"]) > 0, (
                f"{d['name']} missing description"
            )
            assert "input_schema" in d and isinstance(d["input_schema"], dict), (
                f"{d['name']} missing input_schema"
            )
