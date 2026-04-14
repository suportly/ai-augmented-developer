"""Tests for :mod:`aiadev.variable_prompt`."""
from __future__ import annotations

import pytest

from aiadev.variable_prompt import (
    VariableError,
    collect,
    merge_vars_strings,
    parse_cli_vars,
)


# ---------------------------------------------------------------------------
# parse_cli_vars
# ---------------------------------------------------------------------------


class TestParseCliVars:
    def test_empty_returns_empty_dict(self) -> None:
        assert parse_cli_vars("") == {}
        assert parse_cli_vars(None) == {}

    def test_single_pair(self) -> None:
        assert parse_cli_vars("A=1") == {"A": "1"}

    def test_multiple_pairs(self) -> None:
        assert parse_cli_vars("A=1,B=2,C=3") == {"A": "1", "B": "2", "C": "3"}

    def test_strips_whitespace(self) -> None:
        assert parse_cli_vars("  A = 1 ,  B=2  ") == {"A": "1", "B": "2"}

    def test_rejects_entry_without_equals(self) -> None:
        with pytest.raises(VariableError, match="invalid --vars"):
            parse_cli_vars("A=1,BROKEN")

    def test_rejects_empty_key(self) -> None:
        with pytest.raises(VariableError, match="empty key"):
            parse_cli_vars("=value")

    def test_rejects_duplicate_keys(self) -> None:
        with pytest.raises(VariableError, match="duplicate key"):
            parse_cli_vars("A=1,A=2")

    def test_tolerates_trailing_comma(self) -> None:
        assert parse_cli_vars("A=1,,") == {"A": "1"}

    def test_empty_value_is_allowed(self) -> None:
        assert parse_cli_vars("A=") == {"A": ""}


# ---------------------------------------------------------------------------
# merge_vars_strings
# ---------------------------------------------------------------------------


class TestMergeVarsStrings:
    def test_merges_multiple_strings(self) -> None:
        assert merge_vars_strings(["A=1", "B=2"]) == {"A": "1", "B": "2"}

    def test_later_string_overrides_earlier(self) -> None:
        assert merge_vars_strings(["A=1", "A=2"]) == {"A": "2"}

    def test_empty_list(self) -> None:
        assert merge_vars_strings([]) == {}


# ---------------------------------------------------------------------------
# collect
# ---------------------------------------------------------------------------


def _recording_prompt(answers: dict[str, str]):
    """Build a fake prompt_func that returns a scripted answer per prompt text."""

    calls: list[tuple[str, str | None]] = []

    def _fake(text: str, *, default=None, show_default: bool = True) -> str:
        calls.append((text, default))
        return answers.get(text, "")

    _fake.calls = calls  # type: ignore[attr-defined]
    return _fake


def _vars(*entries: dict[str, object]) -> list[dict[str, object]]:
    return list(entries)


class TestCollect:
    def test_cli_value_wins_over_everything(self) -> None:
        preset_vars = _vars(
            {"name": "FOO", "prompt": "Foo", "default": "d", "required": True}
        )
        result = collect(
            preset_vars,
            previous={"FOO": "prev"},
            cli_vars={"FOO": "cli"},
            non_interactive=True,
        )
        assert result == {"FOO": "cli"}

    def test_previous_wins_over_preset_default_in_non_interactive(self) -> None:
        preset_vars = _vars({"name": "FOO", "default": "preset"})
        result = collect(
            preset_vars,
            previous={"FOO": "prev"},
            non_interactive=True,
        )
        assert result == {"FOO": "prev"}

    def test_preset_default_used_when_nothing_else(self) -> None:
        preset_vars = _vars({"name": "FOO", "default": "preset"})
        result = collect(preset_vars, non_interactive=True)
        assert result == {"FOO": "preset"}

    def test_non_interactive_missing_required_raises(self) -> None:
        preset_vars = _vars({"name": "FOO", "required": True})
        with pytest.raises(VariableError, match="required variable 'FOO'"):
            collect(preset_vars, non_interactive=True)

    def test_non_interactive_missing_optional_becomes_empty_string(self) -> None:
        preset_vars = _vars({"name": "FOO"})
        result = collect(preset_vars, non_interactive=True)
        assert result == {"FOO": ""}

    def test_interactive_prompt_uses_previous_as_default(self) -> None:
        preset_vars = _vars(
            {"name": "FOO", "prompt": "Enter FOO", "default": "preset_default"}
        )
        prompt = _recording_prompt({"Enter FOO": "user-answer"})
        result = collect(
            preset_vars,
            previous={"FOO": "from-previous"},
            prompt_func=prompt,
        )
        assert result == {"FOO": "user-answer"}
        # The prompt was offered the previous value as default, not the
        # preset default — previous wins.
        assert prompt.calls[0] == ("Enter FOO", "from-previous")

    def test_interactive_prompt_with_preset_default_when_no_previous(self) -> None:
        preset_vars = _vars({"name": "FOO", "default": "preset"})
        prompt = _recording_prompt({"FOO": "override"})
        result = collect(preset_vars, prompt_func=prompt)
        assert result == {"FOO": "override"}
        assert prompt.calls[0] == ("FOO", "preset")

    def test_interactive_prompt_uses_name_as_text_when_no_prompt(self) -> None:
        preset_vars = _vars({"name": "FOO"})
        prompt = _recording_prompt({"FOO": "value"})
        collect(preset_vars, prompt_func=prompt)
        assert prompt.calls[0][0] == "FOO"

    def test_interactive_required_rejects_empty_answer(self) -> None:
        preset_vars = _vars(
            {"name": "FOO", "prompt": "Enter FOO", "required": True}
        )
        prompt = _recording_prompt({"Enter FOO": ""})
        with pytest.raises(VariableError, match="cannot be empty"):
            collect(preset_vars, prompt_func=prompt)

    def test_missing_name_raises(self) -> None:
        preset_vars = [{"prompt": "no name"}]
        with pytest.raises(VariableError, match="without a name"):
            collect(preset_vars, non_interactive=True)

    def test_preset_default_accepts_non_string_values(self) -> None:
        # preset.yaml may carry a numeric default; collect stringifies it.
        preset_vars = _vars({"name": "PORT", "default": 8080})
        result = collect(preset_vars, non_interactive=True)
        assert result == {"PORT": "8080"}
