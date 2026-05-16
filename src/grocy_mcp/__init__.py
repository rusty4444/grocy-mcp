"""Grocy MCP server package."""

from __future__ import annotations

import os
import sys

from mcp.server.fastmcp import FastMCP

from . import client as api
from .tools import register_tools

mcp = FastMCP("grocy-mcp")
register_tools(mcp)


def main() -> None:
    """Run the Grocy MCP server over stdio."""
    base_url = os.environ.get("GROCY_BASE_URL", "https://demo.grocy.info").strip()
    api_key = os.environ.get("GROCY_API_KEY")
    timeout = float(os.environ.get("GROCY_TIMEOUT", "20"))

    if not base_url:
        print("Error: GROCY_BASE_URL must not be empty", file=sys.stderr)
        sys.exit(1)

    api.configure(base_url=base_url, api_key=api_key, timeout=timeout)
    mcp.run(transport="stdio")


__all__ = ["main", "mcp"]
