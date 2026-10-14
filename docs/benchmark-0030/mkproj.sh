#!/bin/sh
# usage: mkproj.sh <arm> <dest>   (arm: before|after)
set -e
B=$(cd "$(dirname "$0")" && pwd)
ARM=$1; DEST=$2
rm -rf "$DEST"; mkdir -p "$DEST/src/hello_cli" "$DEST/tests"
cd "$DEST"
cat > pyproject.toml <<'P'
[project]
name = "hello-cli"
version = "0.1.0"
dependencies = ["click"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
P
cat > src/hello_cli/__init__.py <<'P'
P
cat > src/hello_cli/cli.py <<'P'
import click


@click.group()
def main():
    """hello-cli: tiny example CLI."""


if __name__ == "__main__":
    main()
P
cat > tests/test_cli.py <<'P'
from click.testing import CliRunner

from hello_cli.cli import main


def test_help_exits_zero():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
P
cat > README.md <<'P'
# hello-cli

Tiny example CLI used to exercise the pipeline.

Run the tests with `python3 -m pytest`.
P
printf '__pycache__/\n.pytest_cache/\n*.pyc\n.aiadev/\n' > .gitignore
git init -q -b main
git config user.email bench@example.com; git config user.name bench; git config commit.gpgsign false
git add -A; git commit -q -m "chore: initial hello-cli"
PATH="$B/bin-$ARM:$PATH" aiadev install --project-root "$DEST" --preset lean --non-interactive --vars PROJECT_NAME=hello-cli >/dev/null
git add -A; git commit -q -m "chore: install ai-augmented-developer ($ARM)"
git checkout -q -b feature/greet
