#!/usr/bin/env python3
"""Live read-only validation against a Grocy instance."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

READ_ONLY_CALLS = [
    ("grocy_system_info", {}),
    ("grocy_list_products", {"limit": 5}),
    ("grocy_search_products", {"query": "c", "limit": 5}),
    ("grocy_get_product", {"product_id": 1}),
    ("grocy_stock_overview", {"limit": 5}),
    ("grocy_volatile_stock", {"limit": 5}),
    ("grocy_product_stock_details", {"product_id": 1}),
    ("grocy_product_stock_entries", {"product_id": 1, "limit": 5}),
    ("grocy_common_entities", {}),
    ("grocy_list_shopping_lists", {"limit": 5}),
    ("grocy_list_shopping_list_items", {"include_done": True, "limit": 5}),
    ("grocy_list_entity", {"entity": "quantity_units", "limit": 5}),
    ("grocy_get_entity_object", {"entity": "products", "object_id": 1}),
]


def call_tool(name: str, args: dict) -> tuple[bool, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env.setdefault("GROCY_BASE_URL", "https://demo.grocy.info")
    messages = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "live-test", "version": "1.0.0"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": name, "arguments": args}},
    ]
    proc = subprocess.Popen(
        [sys.executable, "-m", "grocy_mcp"],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    stdout, stderr = proc.communicate("\n".join(json.dumps(m) for m in messages) + "\n", timeout=45)
    if "Traceback" in stderr:
        return False, stderr
    for line in stdout.splitlines():
        data = json.loads(line)
        if data.get("id") == 2:
            text = data["result"]["content"][0].get("text", "")
            ok = not data["result"].get("isError", False) and not text.startswith("Error")
            return ok, text[:300]
    return False, stdout + stderr


def main() -> int:
    failures = []
    for name, args in READ_ONLY_CALLS:
        ok, text = call_tool(name, args)
        status = "PASS" if ok else "FAIL"
        print(f"{status} {name}: {text.replace(chr(10), ' ')[:180]}")
        if not ok:
            failures.append(name)
    if failures:
        print(f"Failures: {', '.join(failures)}", file=sys.stderr)
        return 1
    print(f"{len(READ_ONLY_CALLS)}/{len(READ_ONLY_CALLS)} live read-only calls passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
