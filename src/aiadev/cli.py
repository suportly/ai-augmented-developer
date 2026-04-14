"""Entry point for the ``aiadev`` CLI."""
from __future__ import annotations

import click

from . import __version__
from .commands.doctor import doctor_command
from .commands.init import init_command
from .commands.install import install_command
from .commands.validate import validate_command


@click.group(help="AI-Augmented Developer CLI.")
@click.version_option(__version__, prog_name="aiadev")
def main() -> None:  # pragma: no cover — thin router
    """Top-level group; subcommands do the work."""


main.add_command(validate_command)
main.add_command(init_command)
main.add_command(install_command)
main.add_command(doctor_command)


if __name__ == "__main__":  # pragma: no cover
    main()
