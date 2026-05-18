# Grocy MCP

<!-- mcp-name: io.github.rusty4444/grocy-mcp -->

A Model Context Protocol (MCP) server for [Grocy](https://grocy.info/), the self-hosted household ERP for groceries, inventory, chores, batteries, recipes, tasks, and shopping lists.

This server focuses on AI-friendly household operations that are awkward through generic REST clients:

- Inspect Grocy system/version status
- List, search, and inspect products
- Read current stock, volatile stock, product stock details, and individual stock entries
- List current shopping list items and add/remove products from shopping lists
- Look up products by barcode/Grocycode
- List and inspect any `/api/objects/{entity}` entity
- Create/update generic entity objects from JSON
- Add, consume, and inventory product stock
- Add/remove product amounts from shopping lists

## Why this exists

Grocy has a strong REST API, but MCP coverage is sparse and usually either incomplete or tightly coupled to one client's workflow. This package gives Hermes, Claude Desktop, Cursor, and other MCP clients a small, explicit, documented tool surface.

## Installation

```bash
pipx install git+https://github.com/rusty4444/grocy-mcp.git
```

Or from a checkout:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

The server reads configuration from environment variables:

| Variable | Required | Default | Description |
|---|---:|---|---|
| `GROCY_BASE_URL` | No | `https://demo.grocy.info` | Grocy base URL, with or without `/api` |
| `GROCY_API_KEY` | No for public/demo read-only instances, yes for private/write access | unset | Grocy API key sent as `GROCY-API-KEY` |
| `GROCY_TIMEOUT` | No | `20` | HTTP timeout in seconds |

Grocy API keys are managed in Grocy under **Manage API keys**. The API accepts the `GROCY-API-KEY` header.

## MCP client config

```json
{
  "mcpServers": {
    "grocy": {
      "command": "grocy-mcp",
      "env": {
        "GROCY_BASE_URL": "https://grocy.example.com",
        "GROCY_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Tools

| Tool | Purpose |
|---|---|
| `grocy_system_info` | Grocy version and runtime details |
| `grocy_list_products` | List configured products |
| `grocy_search_products` | Search products by name/description |
| `grocy_get_product` | Fetch one product object |
| `grocy_lookup_product_by_barcode` | Resolve a barcode/Grocycode |
| `grocy_stock_overview` | Current stock rows |
| `grocy_volatile_stock` | Due, overdue, expired, or missing products |
| `grocy_product_stock_details` | Detailed stock state for one product |
| `grocy_product_stock_entries` | Individual stock entries in next-use order |
| `grocy_common_entities` | Common generic entity names useful with CRUD tools |
| `grocy_list_shopping_lists` | Configured shopping lists |
| `grocy_list_shopping_list_items` | Current shopping list rows, optionally filtered by list id |
| `grocy_list_entity` | List any generic Grocy entity |
| `grocy_get_entity_object` | Fetch any generic entity object |
| `grocy_create_entity_object` | POST a generic entity object from JSON |
| `grocy_update_entity_object` | PUT a generic entity object from JSON |
| `grocy_add_stock` | Add product amount to stock |
| `grocy_consume_stock` | Consume/remove product amount from stock |
| `grocy_inventory_product` | Set product inventory amount |
| `grocy_add_product_to_shopping_list` | Add a product to a shopping list |
| `grocy_remove_product_from_shopping_list` | Remove a product from a shopping list |

## Development and validation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
ruff check .
pytest
python scripts/live_readonly_test.py
```

The live read-only test defaults to `https://demo.grocy.info`, avoiding mutations on shared infrastructure. It has been validated against Grocy API 4.6.0. Use a private Grocy instance plus `GROCY_API_KEY` for write-path testing.

## Safety

Write-capable tools directly mutate Grocy data. Prefer read-only tools when using public demos. Keep `GROCY_API_KEY` in MCP client environment config or a secret manager, never in source control.
