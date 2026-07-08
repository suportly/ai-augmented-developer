"""Pure migrator for SKILL.md frontmatter: old shape -> ``metadata.aiadev``.

Spec: specs/0016-agent-skills-interop/spec.md, Story 1, sc4 + cl-1/cl-5/cl-7.
Plan: ADR-4 — the 5 proprietary aiadev pipeline fields (``version``,
``inputs``, ``outputs``, ``requires``, ``handoffs``) move from the top level
of a SKILL.md frontmatter block into a nested ``metadata.aiadev`` object.
Standard Agent Skills fields (``license``, ``allowed-tools``,
``disable-model-invocation``, ``argument-hint``) and any third-party
``metadata`` keys stay exactly where they are.

``migrate_frontmatter`` is a pure function with no filesystem access, so it
is trivially unit-testable and reusable from multiple call sites:

- the one-shot repo migration of the 22 in-repo ``SKILL.md`` files (T004);
- ``aiadev sync`` auto-migration of already-installed consumer skills (T007).

``migrate_skill_file`` is the file-level helper living in this same module
(per ADR-4): it parses the frontmatter block of a SKILL.md, applies
``migrate_frontmatter``, and rewrites only the frontmatter when something
changed, leaving the Markdown body byte-for-byte untouched.
"""

from __future__ import annotations

from pathlib import Path

import yaml


class FrontmatterError(Exception):
    """Raised on any malformed SKILL.md frontmatter.

    Carries a single-line, actionable message suitable for printing
    directly to the user (same convention as ``tasks_status.TasksMdError``).
    File-level failures name the offending path in the message.
    """


#: The 5 proprietary aiadev pipeline fields that move under
#: ``metadata.aiadev``. Order matters only for the deterministic key
#: ordering applied when re-serializing (see ``_ordered_frontmatter``).
PROPRIETARY_KEYS: tuple[str, ...] = (
    "version",
    "inputs",
    "outputs",
    "requires",
    "handoffs",
)


def migrate_frontmatter(fm: dict) -> tuple[dict, bool]:
    """Move the 5 proprietary pipeline fields into ``metadata.aiadev``.

    Returns ``(new_fm, changed)``. ``new_fm`` is always a new dict (and any
    nested ``metadata``/``metadata.aiadev`` dicts it contains are also new
    objects) — the input ``fm`` is never mutated. ``changed`` is ``True``
    only when the returned dict differs from the input; a frontmatter that
    is already conformant (no proprietary keys at the top level) is
    returned as an equivalent dict with ``changed=False``.

    Fields left untouched at their current location: ``name``,
    ``description``, ``license``, ``compatibility``, ``allowed-tools``,
    ``disable-model-invocation``, ``argument-hint``, and any third-party
    keys already nested under ``metadata`` (everything except the
    ``aiadev`` namespace).

    Duplicate-key precedence rule: if a proprietary key is present BOTH at
    the top level AND already under ``metadata.aiadev``, that state is
    ambiguous by construction (two candidate values for the same field).
    This function resolves it by preferring the existing
    ``metadata.aiadev`` value (treated as authoritative — it is the
    already-migrated, presumably more recent, value) and dropping the
    stale top-level duplicate. Because the top-level key is removed either
    way, this case is still reported as ``changed=True``.

    Idempotent: calling ``migrate_frontmatter`` on the output of a previous
    call always returns ``(equivalent_dict, False)``.

    Raises :class:`FrontmatterError` when ``fm`` is not a mapping (YAML
    frontmatter can legally parse to a list or scalar; those are not valid
    skill frontmatter).
    """
    if not isinstance(fm, dict):
        raise FrontmatterError(
            "ERROR: frontmatter is not a mapping "
            f"(got {type(fm).__name__}); SKILL.md frontmatter must be a "
            "YAML mapping with at least 'name' and 'description'."
        )

    top_level_proprietary = [key for key in PROPRIETARY_KEYS if key in fm]

    existing_metadata = fm.get("metadata")
    has_metadata = isinstance(existing_metadata, dict)
    existing_aiadev = existing_metadata.get("aiadev") if has_metadata else None
    has_aiadev = isinstance(existing_aiadev, dict)

    if not top_level_proprietary and not has_metadata:
        # Truly minimal frontmatter, nothing to move and no metadata to
        # preserve: return an equivalent (but distinct) dict, unchanged.
        return dict(fm), False

    if not top_level_proprietary and has_metadata:
        # metadata may already contain aiadev or third-party keys; either
        # way there is nothing new to move. Deep-copy metadata so the
        # returned dict does not alias the input's nested objects.
        new_fm = {k: v for k, v in fm.items() if k != "metadata"}
        new_fm["metadata"] = _deep_copy_metadata(existing_metadata)
        return new_fm, False

    # There is at least one proprietary key at the top level: a migration
    # is required. Build the new aiadev namespace starting from whatever
    # already exists there (authoritative on conflict), then fill in any
    # top-level values for keys not already present under aiadev.
    new_aiadev: dict = dict(existing_aiadev) if has_aiadev else {}
    for key in top_level_proprietary:
        if key not in new_aiadev:
            new_aiadev[key] = fm[key]
        # else: metadata.aiadev already had this key -> keep it (existing
        # value wins per the duplicate-key precedence rule), top-level
        # duplicate is simply dropped below.

    new_metadata = _deep_copy_metadata(existing_metadata) if has_metadata else {}
    new_metadata["aiadev"] = new_aiadev

    new_fm = {
        k: v
        for k, v in fm.items()
        if k not in PROPRIETARY_KEYS and k != "metadata"
    }
    new_fm["metadata"] = new_metadata

    return new_fm, True


def _deep_copy_metadata(metadata: dict) -> dict:
    """Shallow-safe copy of a ``metadata`` mapping.

    Copies the top-level dict and its immediate ``aiadev`` sub-dict (if
    present) so callers never alias the input's mutable containers. Values
    within third-party keys are left as-is (they are opaque to us and, per
    the open standard, expected to be simple string values anyway).
    """
    new_metadata = dict(metadata)
    aiadev = metadata.get("aiadev")
    if isinstance(aiadev, dict):
        new_metadata["aiadev"] = dict(aiadev)
    return new_metadata


def _ordered_frontmatter(fm: dict) -> dict:
    """Return ``fm`` with a deterministic top-level key order.

    Rule: ``name`` and ``description`` always come first (in that order,
    when present). Every other original top-level key keeps its relative
    order, except ``metadata`` which is always moved to the end — this
    keeps the common case (a short list of standard fields followed by the
    aiadev namespace) readable and stable across repeated migrations,
    regardless of whether ``metadata`` was already present in the input or
    newly created by ``migrate_frontmatter``.
    """
    ordered: dict = {}
    for key in ("name", "description"):
        if key in fm:
            ordered[key] = fm[key]
    for key, value in fm.items():
        if key in ("name", "description", "metadata"):
            continue
        ordered[key] = value
    if "metadata" in fm:
        ordered["metadata"] = fm["metadata"]
    return ordered


def _split_frontmatter(text: str, path: Path) -> tuple[str, str, str]:
    """Split ``text`` into (frontmatter_yaml, body, line_ending_used).

    ``text`` must start with a ``---`` delimiter line. Returns the raw YAML
    text between the delimiters (no leading/trailing ``---`` lines) and the
    remainder of the file starting right after the closing ``---`` line's
    newline, so the body can be reattached byte-for-byte.

    Raises :class:`FrontmatterError` (message names ``path``) when the file
    has no frontmatter block or the block is never closed.
    """
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(newline)
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError(
            f"ERROR: {path}: missing YAML frontmatter — the file must start "
            "with a '---' delimiter line."
        )

    closing_index = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = i
            break
    if closing_index is None:
        raise FrontmatterError(
            f"ERROR: {path}: unterminated YAML frontmatter — no closing "
            "'---' delimiter found."
        )

    fm_text = newline.join(lines[1:closing_index])
    body = newline.join(lines[closing_index + 1 :])
    return fm_text, body, newline


def migrate_skill_file(path: Path) -> bool:
    """Migrate the frontmatter of the SKILL.md at ``path`` in place.

    Parses the YAML frontmatter block (between the first ``---`` pair),
    applies :func:`migrate_frontmatter`, and rewrites the file only when
    something changed. The Markdown body is preserved byte-for-byte: only
    the frontmatter block is re-serialized.

    Known limitation: YAML comments inside the frontmatter block do NOT
    survive a rewrite (``yaml.safe_load`` discards them). Files that are
    already conformant are never rewritten, so their comments are safe;
    when a file with in-frontmatter comments is migrated, restore the
    comments manually afterwards if they matter.

    Returns ``True`` when the file was rewritten, ``False`` when it was
    already conformant (file left untouched).

    Raises :class:`FrontmatterError` (single-line message naming ``path``)
    on malformed YAML frontmatter, missing/unterminated frontmatter block,
    or frontmatter that is not a mapping.
    """
    original_text = path.read_text(encoding="utf-8")
    fm_text, body, newline = _split_frontmatter(original_text, path)

    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        summary = str(exc).replace("\n", " ").strip()
        raise FrontmatterError(
            f"ERROR: {path}: malformed YAML frontmatter — fix the YAML "
            f"before migrating ({summary})."
        ) from exc
    if not isinstance(fm, dict):
        raise FrontmatterError(
            f"ERROR: {path}: frontmatter is not a mapping "
            f"(got {type(fm).__name__}); SKILL.md frontmatter must be a "
            "YAML mapping with at least 'name' and 'description'."
        )
    new_fm, changed = migrate_frontmatter(fm)
    if not changed:
        return False

    ordered = _ordered_frontmatter(new_fm)
    serialized = yaml.safe_dump(
        ordered,
        sort_keys=False,
        allow_unicode=True,
        width=1_000_000,
        default_flow_style=False,
    )
    # yaml.safe_dump always uses "\n"; normalize to the file's line ending.
    if newline != "\n":
        serialized = serialized.replace("\n", newline)

    new_text = f"---{newline}{serialized}---{newline}{body}"
    path.write_text(new_text, encoding="utf-8")
    return True
