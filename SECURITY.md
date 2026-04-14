# Security Policy

## Supported versions

Only the latest minor release receives security updates. During the v0.x series, only the most recent tag on `main` is considered supported.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a vulnerability

This project ships prompts, templates, and (from v0.2) a Python CLI. Potential security concerns include, but are not limited to:

- **Prompt injection vectors** in skills or templates that could make a user's agent leak secrets or perform unintended actions.
- **Command injection** in the `aiadev` CLI when substituting preset variables or reading user-supplied files.
- **Dependency vulnerabilities** in `pyproject.toml` once the CLI ships.
- **Credential exposure** in example files, fixtures, or bundled presets.

### How to report

- **Do not open a public GitHub issue** for security-sensitive reports.
- Open a private security advisory at <https://github.com/alairjt/ai-augmented-developer/security/advisories/new>, or
- Email the maintainer (address in `pyproject.toml` once available; until then, contact via GitHub profile).

Please include:

1. A description of the issue and its potential impact.
2. Steps to reproduce, ideally with a minimal example.
3. The version (commit hash or tag) you tested against.
4. Any suggested mitigation.

### What to expect

- Acknowledgement within 5 business days.
- Triage and severity assessment within 10 business days.
- A target fix date communicated back before work starts.
- Credit in `CHANGELOG.md` (opt-in) once the fix is released.

## Scope

This policy covers the repository at `github.com/alairjt/ai-augmented-developer` and any package published from it (`aiadev` on PyPI from v0.2). Third-party agents, skills, or presets installed via extensions are the responsibility of their respective maintainers.
