"""MCP tools for Grocy."""

from __future__ import annotations

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from . import client as api

WritableEntity = Annotated[
    str,
    Field(
        description=(
            "Grocy generic entity name, for example products, quantity_units, locations, "
            "shopping_list, shopping_lists, chores, batteries, equipment, recipes"
        )
    ),
]


def register_tools(mcp: FastMCP) -> None:
    """Register all Grocy tools."""

    @mcp.tool()
    async def grocy_system_info() -> str:
        """Return Grocy version and server runtime information."""
        try:
            return _json(api.system_info())
        except Exception as exc:
            return f"Error getting Grocy system info: {exc}"

    @mcp.tool()
    async def grocy_list_products(
        active_only: Annotated[bool, Field(description="Only include products where active=1")] = True,
        limit: Annotated[int, Field(description="Maximum number of products to return, 1-500")] = 100,
        offset: Annotated[int, Field(description="Number of matching products to skip before returning results")] = 0,
    ) -> str:
        """List products configured in Grocy."""
        try:
            products = api.list_objects("products")
            if active_only:
                products = [p for p in products if int(p.get("active", 1) or 0) == 1]
            return _format_products(_page(products, limit, offset))
        except Exception as exc:
            return f"Error listing Grocy products: {exc}"

    @mcp.tool()
    async def grocy_search_products(
        query: Annotated[str, Field(description="Case-insensitive product name or description substring")],
        limit: Annotated[int, Field(description="Maximum number of matching products to return, 1-100")] = 25,
        offset: Annotated[int, Field(description="Number of matching products to skip before returning results")] = 0,
    ) -> str:
        """Search Grocy products by name or description."""
        try:
            q = query.strip().lower()
            products = api.list_objects("products")
            matches = [
                p
                for p in products
                if q in str(p.get("name", "")).lower() or q in str(p.get("description", "")).lower()
            ]
            return _format_products(_page(matches, limit, offset, max_limit=100))
        except Exception as exc:
            return f"Error searching Grocy products: {exc}"

    @mcp.tool()
    async def grocy_get_product(
        product_id: Annotated[int, Field(description="Grocy product id")],
    ) -> str:
        """Get one Grocy product object by id."""
        try:
            return _json(api.get_object("products", product_id))
        except Exception as exc:
            return f"Error getting Grocy product {product_id}: {exc}"

    @mcp.tool()
    async def grocy_lookup_product_by_barcode(
        barcode: Annotated[str, Field(description="Barcode, Grocycode, or product barcode to resolve")],
    ) -> str:
        """Look up a product using Grocy's stock barcode endpoint."""
        try:
            return _json(api.product_by_barcode(barcode))
        except Exception as exc:
            return f"Error looking up barcode {barcode}: {exc}"

    @mcp.tool()
    async def grocy_stock_overview(
        include_zero_stock: Annotated[bool, Field(description="Include products with amount 0 when returned by the Grocy server")] = True,
        limit: Annotated[int, Field(description="Maximum number of stock rows to return, 1-500")] = 100,
        offset: Annotated[int, Field(description="Number of stock rows to skip before returning results")] = 0,
    ) -> str:
        """Return current Grocy stock rows with amounts and due dates."""
        try:
            rows = api.list_stock()
            if not include_zero_stock:
                rows = [r for r in rows if float(r.get("amount") or 0) > 0]
            return _format_stock(_page(rows, limit, offset))
        except Exception as exc:
            return f"Error getting Grocy stock: {exc}"

    @mcp.tool()
    async def grocy_volatile_stock(
        limit: Annotated[int, Field(description="Maximum number of due/overdue/missing rows to return, 1-500")] = 100,
        offset: Annotated[int, Field(description="Number of volatile stock rows to skip before returning results")] = 0,
    ) -> str:
        """Return products due soon, overdue, expired, or missing according to Grocy."""
        try:
            return _format_stock(_page(api.volatile_stock(), limit, offset))
        except Exception as exc:
            return f"Error getting Grocy volatile stock: {exc}"

    @mcp.tool()
    async def grocy_product_stock_details(
        product_id: Annotated[int, Field(description="Grocy product id")],
    ) -> str:
        """Get detailed stock state for one Grocy product."""
        try:
            return _json(api.product_stock_details(product_id))
        except Exception as exc:
            return f"Error getting stock details for product {product_id}: {exc}"

    @mcp.tool()
    async def grocy_product_stock_entries(
        product_id: Annotated[int, Field(description="Grocy product id")],
        limit: Annotated[int, Field(description="Maximum number of stock entries to return, 1-200")] = 50,
        offset: Annotated[int, Field(description="Number of stock entries to skip before returning results")] = 0,
    ) -> str:
        """List individual stock entries for a product in next-use order."""
        try:
            return _json(_page(api.product_stock_entries(product_id), limit, offset, max_limit=200))
        except Exception as exc:
            return f"Error getting stock entries for product {product_id}: {exc}"

    @mcp.tool()
    async def grocy_common_entities() -> str:
        """List common Grocy generic entity names for use with grocy_list_entity and CRUD tools."""
        entities = [
            "products",
            "quantity_units",
            "locations",
            "shopping_list",
            "shopping_lists",
            "product_groups",
            "chores",
            "batteries",
            "equipment",
            "recipes",
            "tasks",
            "meal_plan",
            "userfields",
            "userentities",
        ]
        return _json(entities)

    @mcp.tool()
    async def grocy_list_shopping_lists(
        limit: Annotated[int, Field(description="Maximum number of shopping lists to return, 1-500")] = 100,
        offset: Annotated[int, Field(description="Number of shopping lists to skip before returning results")] = 0,
    ) -> str:
        """List configured Grocy shopping lists."""
        try:
            return _json(_page(api.list_objects("shopping_lists"), limit, offset))
        except Exception as exc:
            return f"Error listing Grocy shopping lists: {exc}"

    @mcp.tool()
    async def grocy_list_shopping_list_items(
        list_id: Annotated[int | None, Field(description="Optional Grocy shopping list id to filter by; 1 is usually the default list")] = None,
        include_done: Annotated[bool, Field(description="Include completed/done shopping list items")] = False,
        limit: Annotated[int, Field(description="Maximum number of shopping list items to return, 1-500")] = 100,
        offset: Annotated[int, Field(description="Number of matching shopping list items to skip before returning results")] = 0,
    ) -> str:
        """List current Grocy shopping list items."""
        try:
            items = api.list_objects("shopping_list")
            products = {p.get("id"): p.get("name") for p in api.list_objects("products")}
            if list_id is not None:
                items = [i for i in items if int(i.get("shopping_list_id") or 0) == list_id]
            if not include_done:
                items = [i for i in items if int(i.get("done") or 0) == 0]
            for item in items:
                item["product_name"] = products.get(item.get("product_id"))
            return _json(_page(items, limit, offset))
        except Exception as exc:
            return f"Error listing Grocy shopping list items: {exc}"

    @mcp.tool()
    async def grocy_list_entity(
        entity: WritableEntity,
        limit: Annotated[int, Field(description="Maximum number of rows to return, 1-500")] = 100,
        offset: Annotated[int, Field(description="Number of entity rows to skip before returning results")] = 0,
    ) -> str:
        """List any Grocy generic entity exposed by /api/objects/{entity}."""
        try:
            return _json(_page(api.list_objects(entity), limit, offset))
        except Exception as exc:
            return f"Error listing Grocy entity {entity}: {exc}"

    @mcp.tool()
    async def grocy_get_entity_object(
        entity: WritableEntity,
        object_id: Annotated[int, Field(description="Object id inside the selected Grocy entity")],
    ) -> str:
        """Get any Grocy generic entity object by id."""
        try:
            return _json(api.get_object(entity, object_id))
        except Exception as exc:
            return f"Error getting Grocy entity {entity}/{object_id}: {exc}"

    @mcp.tool()
    async def grocy_create_entity_object(
        entity: WritableEntity,
        payload_json: Annotated[str, Field(description="JSON object payload to POST to /api/objects/{entity}")],
    ) -> str:
        """Create a Grocy generic entity object from a JSON payload."""
        try:
            payload = _parse_object(payload_json)
            return _json(api.create_object(entity, payload))
        except Exception as exc:
            return f"Error creating Grocy entity {entity}: {exc}"

    @mcp.tool()
    async def grocy_update_entity_object(
        entity: WritableEntity,
        object_id: Annotated[int, Field(description="Object id inside the selected Grocy entity")],
        payload_json: Annotated[str, Field(description="JSON object payload to PUT to /api/objects/{entity}/{object_id}")],
    ) -> str:
        """Update a Grocy generic entity object from a JSON payload."""
        try:
            payload = _parse_object(payload_json)
            return _json(api.update_object(entity, object_id, payload))
        except Exception as exc:
            return f"Error updating Grocy entity {entity}/{object_id}: {exc}"

    @mcp.tool()
    async def grocy_add_stock(
        product_id: Annotated[int, Field(description="Grocy product id to add to stock")],
        amount: Annotated[float, Field(description="Amount to add, in the product's stock quantity unit")],
        best_before_date: Annotated[str | None, Field(description="Optional best-before/due date in YYYY-MM-DD format")] = None,
        price: Annotated[float | None, Field(description="Optional unit price in the configured Grocy currency")] = None,
        location_id: Annotated[int | None, Field(description="Optional Grocy location id; defaults to the product's default location")] = None,
    ) -> str:
        """Add an amount of a product to Grocy stock."""
        try:
            payload = _drop_none({"amount": amount, "best_before_date": best_before_date, "price": price, "location_id": location_id})
            return _json(api.add_stock(product_id, payload))
        except Exception as exc:
            return f"Error adding stock for product {product_id}: {exc}"

    @mcp.tool()
    async def grocy_consume_stock(
        product_id: Annotated[int, Field(description="Grocy product id to remove from stock")],
        amount: Annotated[float, Field(description="Amount to remove, in the product's stock quantity unit")],
        spoiled: Annotated[bool, Field(description="Mark the consumed amount as spoiled waste")] = False,
        location_id: Annotated[int | None, Field(description="Optional location id to consume from")] = None,
    ) -> str:
        """Consume/remove an amount of a product from Grocy stock."""
        try:
            payload = _drop_none({"amount": amount, "spoiled": spoiled, "location_id": location_id})
            return _json(api.consume_stock(product_id, payload))
        except Exception as exc:
            return f"Error consuming stock for product {product_id}: {exc}"

    @mcp.tool()
    async def grocy_inventory_product(
        product_id: Annotated[int, Field(description="Grocy product id to inventory")],
        new_amount: Annotated[float, Field(description="New total current amount for the product")],
        best_before_date: Annotated[str | None, Field(description="Optional best-before date used if products are added")] = None,
        location_id: Annotated[int | None, Field(description="Optional location id used if products are added")] = None,
    ) -> str:
        """Set the inventory amount for a Grocy product."""
        try:
            payload = _drop_none({"new_amount": new_amount, "best_before_date": best_before_date, "location_id": location_id})
            return _json(api.inventory_product(product_id, payload))
        except Exception as exc:
            return f"Error inventorying product {product_id}: {exc}"

    @mcp.tool()
    async def grocy_add_product_to_shopping_list(
        product_id: Annotated[int, Field(description="Grocy product id to add to the shopping list")],
        product_amount: Annotated[float, Field(description="Amount to add, related to the product's stock quantity unit")] = 1,
        list_id: Annotated[int, Field(description="Grocy shopping list id; 1 is usually the default list")] = 1,
        note: Annotated[str | None, Field(description="Optional note for the shopping list item")] = None,
    ) -> str:
        """Add a product amount to a Grocy shopping list."""
        try:
            payload = _drop_none({"product_id": product_id, "product_amount": product_amount, "list_id": list_id, "note": note})
            return _json(api.add_to_shopping_list(payload))
        except Exception as exc:
            return f"Error adding product {product_id} to shopping list: {exc}"

    @mcp.tool()
    async def grocy_remove_product_from_shopping_list(
        product_id: Annotated[int, Field(description="Grocy product id to remove from the shopping list")],
        product_amount: Annotated[float, Field(description="Amount to remove, related to the product's stock quantity unit")] = 1,
        list_id: Annotated[int, Field(description="Grocy shopping list id; 1 is usually the default list")] = 1,
    ) -> str:
        """Remove a product amount from a Grocy shopping list."""
        try:
            payload = {"product_id": product_id, "product_amount": product_amount, "list_id": list_id}
            return _json(api.remove_from_shopping_list(payload))
        except Exception as exc:
            return f"Error removing product {product_id} from shopping list: {exc}"


def _drop_none(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


def _parse_object(payload_json: str) -> dict[str, Any]:
    data = json.loads(payload_json)
    if not isinstance(data, dict):
        raise ValueError("payload_json must decode to a JSON object")
    return data


def _page(rows: list[dict[str, Any]], limit: int, offset: int = 0, max_limit: int = 500) -> list[dict[str, Any]]:
    start = max(0, offset)
    size = max(1, min(limit, max_limit))
    return rows[start : start + size]


def _json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def _format_products(products: list[dict[str, Any]]) -> str:
    if not products:
        return "No products found."
    lines = [f"Products ({len(products)} shown):"]
    for p in products:
        lines.append(
            f"- #{p.get('id')} {p.get('name')}"
            f" | active={p.get('active')} | location_id={p.get('location_id')}"
            f" | min_stock={p.get('min_stock_amount')}"
        )
    return "\n".join(lines)


def _format_stock(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No stock rows found."
    lines = [f"Stock rows ({len(rows)} shown):"]
    for r in rows:
        product = r.get("product") or {}
        product_name = product.get("name") or r.get("product_name") or f"product #{r.get('product_id')}"
        lines.append(
            f"- #{r.get('product_id')} {product_name}: amount={r.get('amount')}"
            f" opened={r.get('amount_opened')} due={r.get('best_before_date')} value={r.get('value')}"
        )
    return "\n".join(lines)
