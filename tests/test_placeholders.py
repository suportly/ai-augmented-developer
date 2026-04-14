"""Tests for :mod:`aiadev.placeholders`.

The module is a pure-function helper used by the install engine. Every
branch is covered here so that ``--cov-fail-under`` does not slip when
the engine lands.
"""
from __future__ import annotations

import pytest

from aiadev.placeholders import find_unresolved, substitute


class TestSubstitute:
    def test_replaces_single_placeholder(self) -> None:
        assert substitute("Hello {{NAME}}!", {"NAME": "world"}) == "Hello world!"

    def test_replaces_multiple_placeholders(self) -> None:
        result = substitute(
            "{{GREETING}} {{NAME}}!", {"GREETING": "Hi", "NAME": "Ada"}
        )
        assert result == "Hi Ada!"

    def test_replaces_repeated_placeholder(self) -> None:
        assert substitute("{{X}} and {{X}}", {"X": "a"}) == "a and a"

    def test_leaves_unknown_placeholder_unchanged(self) -> None:
        assert substitute("{{FOO}} {{BAR}}", {"FOO": "x"}) == "x {{BAR}}"

    def test_empty_values_dict_leaves_text_alone(self) -> None:
        assert substitute("{{FOO}}", {}) == "{{FOO}}"

    def test_empty_text_returns_empty_string(self) -> None:
        assert substitute("", {"FOO": "x"}) == ""

    def test_value_containing_braces_is_not_reinjected(self) -> None:
        # Design decision from the plan: single-pass substitution. A value
        # whose contents look like a placeholder must not be scanned a
        # second time.
        result = substitute(
            "{{FOO}}{{BAR}}", {"FOO": "{{BAR}}", "BAR": "baz"}
        )
        assert result == "{{BAR}}baz"

    def test_doubled_braces_leave_outer_literal(self) -> None:
        # "{{{{FOO}}}}" parses as literal '{{' + '{{FOO}}' + '}}'; the
        # inner placeholder substitutes, outer braces stay.
        assert substitute("{{{{FOO}}}}", {"FOO": "x"}) == "{{x}}"

    def test_lowercase_token_is_not_a_placeholder(self) -> None:
        # The placeholder grammar is UPPER_SNAKE; lowercase tokens are
        # prose, not templates.
        assert substitute("{{foo}}", {"foo": "x"}) == "{{foo}}"

    def test_placeholder_with_digits_after_first_char(self) -> None:
        assert substitute("{{API_V2_URL}}", {"API_V2_URL": "x"}) == "x"

    def test_first_character_must_be_letter(self) -> None:
        # Leading digit is not a valid placeholder key.
        assert substitute("{{2FOO}}", {"2FOO": "x"}) == "{{2FOO}}"

    def test_does_not_mutate_the_values_dict(self) -> None:
        values = {"X": "1"}
        substitute("{{X}}", values)
        assert values == {"X": "1"}

    def test_substitution_value_may_be_empty(self) -> None:
        assert substitute("prefix {{X}} suffix", {"X": ""}) == "prefix  suffix"

    def test_multiline_text(self) -> None:
        text = "line1 {{A}}\nline2 {{B}}\nline3 {{A}}"
        result = substitute(text, {"A": "1", "B": "2"})
        assert result == "line1 1\nline2 2\nline3 1"


class TestFindUnresolved:
    def test_empty_text_returns_empty_list(self) -> None:
        assert find_unresolved("") == []

    def test_plain_text_returns_empty_list(self) -> None:
        assert find_unresolved("no placeholders here") == []

    def test_returns_sorted_unique_keys(self) -> None:
        text = "{{FOO}} {{BAR}} {{FOO}} {{BAZ}}"
        assert find_unresolved(text) == ["BAR", "BAZ", "FOO"]

    def test_ignores_lowercase_tokens(self) -> None:
        assert find_unresolved("{{foo}} and {{BAR}}") == ["BAR"]

    def test_ignores_leading_digit_tokens(self) -> None:
        assert find_unresolved("{{2FOO}} {{BAR}}") == ["BAR"]
