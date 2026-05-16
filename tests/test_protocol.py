"""MCP protocol and tool schema tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_mcp(messages: list[dict]) -> list[dict]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env.setdefault("GROCY_BASE_URL", "https://demo.grocy.info")
    proc = subprocess.Popen(
        [sys.executable, "-m", "grocy_mcp"],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    assert proc.stdin is not None
    assert proc.stdout is not None
    payload = "\n".join(json.dumps(m) for m in messages) + "\n"
    stdout, stderr = proc.communicate(payload, timeout=30)
    proc.kill()
    assert "Traceback" not in stderr
    return [json.loads(line) for line in stdout.splitlines() if line.strip()]


def test_tools_list_has_complete_descriptions() -> None:
    messages = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "1.0.0"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]
    responses = _run_mcp(messages)
    listed = next(r for r in responses if r.get("id") == 2)
    tools = listed["result"]["tools"]

    assert len(tools) >= 21
    names = {t["name"] for t in tools}
    assert "grocy_system_info" in names
    assert "grocy_add_stock" in names
    assert "grocy_common_entities" in names
    assert "grocy_list_shopping_lists" in names
    assert "grocy_list_shopping_list_items" in names
    assert "grocy_add_product_to_shopping_list" in names

    for tool in tools:
        assert tool.get("description"), f"missing tool description: {tool['name']}"
        properties = tool.get("inputSchema", {}).get("properties", {})
        for param_name, schema in properties.items():
            assert schema.get("description"), f"{tool['name']}.{param_name} missing description"


def test_readonly_tool_call_against_demo() -> None:
    messages = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "1.0.0"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "grocy_system_info", "arguments": {}},
        },
    ]
    responses = _run_mcp(messages)
    call = next(r for r in responses if r.get("id") == 2)
    text = call["result"]["content"][0]["text"]
    assert "grocy_version" in text
    assert not call["result"].get("isError", False)
