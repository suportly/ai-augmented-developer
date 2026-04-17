"""FastMCP server exposing the 8 pipeline skills as prompts and tools."""
from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from aiadev.paths import find_framework_root
from aiadev.tools._definitions import list_definitions

_app: FastMCP | None = None


def _make_handler(skill_name: str) -> Any:
    """Create a typed handler function for a pipeline skill."""

    def handler(
        workspace_path: str,
        demand: str = "",
        spec_path: str = "",
        plan_path: str = "",
        language: str = "en",
    ) -> str:
        from aiadev.tools import _call

        kwargs: dict[str, Any] = {}
        if demand:
            kwargs["demand"] = demand
        if spec_path:
            kwargs["spec_path"] = spec_path
        if plan_path:
            kwargs["plan_path"] = plan_path
        if language != "en":
            kwargs["language"] = language
        result = _call(skill_name, workspace_path, **kwargs)
        return json.dumps(result, ensure_ascii=False)

    handler.__name__ = f"{skill_name}_handler"
    handler.__qualname__ = f"{skill_name}_handler"
    return handler


def create_server(framework_root: Any = None) -> FastMCP:
    """Build and return a configured FastMCP server instance."""
    root = framework_root or find_framework_root()
    mcp = FastMCP("aiadev", instructions="AI-Augmented Developer pipeline tools")

    for defn in list_definitions(root):
        name = defn["name"]
        description = defn["description"]
        handler = _make_handler(name)
        mcp.add_tool(handler, name=name, description=description)
        prompt_handler = _make_handler(name)
        mcp.prompt(name=name, description=description)(prompt_handler)

    return mcp


def get_server() -> FastMCP:
    """Return (and cache) the global server instance."""
    global _app
    if _app is None:
        _app = create_server()
    return _app
