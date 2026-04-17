"""Entry point for ``python -m aiadev.mcp_server`` and ``aiadev-mcp-server``."""
from __future__ import annotations

import sys


def main() -> None:
    try:
        from mcp.server.fastmcp import FastMCP  # noqa: F401
    except ImportError:
        print(
            "error: the 'mcp' package is not installed.\n"
            "Install it with: pip install 'aiadev[mcp]'",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        from aiadev.paths import find_framework_root
        find_framework_root()
    except Exception as exc:
        print(f"error: cannot locate aiadev framework root: {exc}", file=sys.stderr)
        sys.exit(1)

    from .server import create_server
    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
