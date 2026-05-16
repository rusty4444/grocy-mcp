---
name: grocy
description: Use the Grocy MCP server for household inventory, stock, products, recipes, chores, batteries, tasks, and shopping lists.
version: 0.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [grocy, mcp, inventory, groceries, shopping-list, household]
---

# Grocy MCP Skill

Use this skill when the user asks Hermes to connect to or automate Grocy.

## Setup

Configure the MCP server with:

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

`GROCY_BASE_URL` may include or omit `/api`. `GROCY_API_KEY` is required for private instances and write operations.

## Tool selection

- Product discovery: `grocy_list_products`, `grocy_search_products`, `grocy_get_product`
- Stock status: `grocy_stock_overview`, `grocy_volatile_stock`, `grocy_product_stock_details`, `grocy_product_stock_entries`
- Barcode lookup: `grocy_lookup_product_by_barcode`
- Shopping list reads: `grocy_list_shopping_lists`, `grocy_list_shopping_list_items`
- Shopping list changes: `grocy_add_product_to_shopping_list`, `grocy_remove_product_from_shopping_list`
- Stock mutations: `grocy_add_stock`, `grocy_consume_stock`, `grocy_inventory_product`
- Advanced Grocy records: `grocy_common_entities`, `grocy_list_entity`, `grocy_get_entity_object`, `grocy_create_entity_object`, `grocy_update_entity_object`

## Pitfalls

- Write tools mutate live household data. Confirm product id, amount, and list id before destructive stock changes.
- Grocy generic entity names are plural table names such as `products`, `quantity_units`, `locations`, `shopping_list`, `shopping_lists`, `chores`, `batteries`, and `equipment`.
- For generic create/update, pass a JSON object string, not YAML or free-form prose.
