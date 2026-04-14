"""Per-platform install handlers.

Each module here (``claude_code``, future ``cursor``, ``codex``,
``opencode``, ``gemini``) owns two responsibilities for its target:

* ``iter_preset_artifacts(preset_root)`` — enumerate the files this
  platform installs from a preset, tagged with role and name.
* ``resolve_target(role, name, project_root)`` — compute where a
  given artifact lands in the consumer project.

The install engine holds everything else: variable collection,
placeholder substitution, sha256 tracking, manifest updates.
"""
