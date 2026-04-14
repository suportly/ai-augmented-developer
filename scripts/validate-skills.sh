#!/usr/bin/env bash
# Thin wrapper around scripts/validate_skills.py so CI and humans share one
# entry point. The real validator is in Python to avoid a yq dependency.

set -euo pipefail

exec python3 "$(dirname "$0")/validate_skills.py" "$@"
