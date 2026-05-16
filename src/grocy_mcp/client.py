"""Thin Grocy REST API client."""

from __future__ import annotations

import os
from typing import Any

import httpx

_BASE_URL: str | None = None
_API_KEY: str | None = None
_TIMEOUT = 20.0


class GrocyError(RuntimeError):
    """Raised when the Grocy API returns an error."""


def configure(base_url: str | None = None, api_key: str | None = None, timeout: float | None = None) -> None:
    """Configure the Grocy API client."""
    global _BASE_URL, _API_KEY, _TIMEOUT
    if base_url is not None:
        _BASE_URL = base_url.rstrip("/")
    if api_key is not None:
        _API_KEY = api_key
    if timeout is not None:
        _TIMEOUT = timeout


def _api_base() -> str:
    base = (_BASE_URL or os.environ.get("GROCY_BASE_URL") or "https://demo.grocy.info").rstrip("/")
    if base.endswith("/api"):
        return base
    return f"{base}/api"


def _api_key() -> str | None:
    return _API_KEY or os.environ.get("GROCY_API_KEY")


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    key = _api_key()
    if key:
        headers["GROCY-API-KEY"] = key
    return headers


def _request(method: str, path: str, **kwargs: Any) -> Any:
    url = f"{_api_base()}{path}"
    try:
        response = httpx.request(method, url, headers=_headers(), timeout=_TIMEOUT, **kwargs)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        body = exc.response.text[:500]
        raise GrocyError(f"{method} {path} failed: HTTP {exc.response.status_code}: {body}") from exc
    except httpx.HTTPError as exc:
        raise GrocyError(f"{method} {path} failed: {exc}") from exc

    if response.status_code == 204 or not response.content:
        return {"ok": True}
    ctype = response.headers.get("content-type", "")
    if "json" in ctype:
        return response.json()
    text = response.text.strip()
    return {"ok": True, "text": text} if text else {"ok": True}


def system_info() -> dict[str, Any]:
    return _request("GET", "/system/info")


def db_changed_time() -> dict[str, Any]:
    return _request("GET", "/system/db-changed-time")


def list_objects(entity: str) -> list[dict[str, Any]]:
    data = _request("GET", f"/objects/{entity}")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return list(data.values()) if all(isinstance(v, dict) for v in data.values()) else [data]
    return []


def get_object(entity: str, object_id: int | str) -> dict[str, Any]:
    data = _request("GET", f"/objects/{entity}/{object_id}")
    if not isinstance(data, dict):
        raise GrocyError(f"Expected object response for {entity}/{object_id}, got {type(data).__name__}")
    return data


def create_object(entity: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = _request("POST", f"/objects/{entity}", json=payload)
    if isinstance(data, dict):
        return data
    return {"ok": True, "response": data}


def update_object(entity: str, object_id: int | str, payload: dict[str, Any]) -> dict[str, Any]:
    data = _request("PUT", f"/objects/{entity}/{object_id}", json=payload)
    if isinstance(data, dict):
        if data.get("ok") and len(data) <= 2:
            return get_object(entity, object_id)
        return data
    return get_object(entity, object_id)


def list_stock() -> list[dict[str, Any]]:
    data = _request("GET", "/stock")
    return data if isinstance(data, list) else []


def volatile_stock() -> list[dict[str, Any]]:
    data = _request("GET", "/stock/volatile")
    return data if isinstance(data, list) else []


def product_stock_details(product_id: int) -> dict[str, Any]:
    data = _request("GET", f"/stock/products/{product_id}")
    if not isinstance(data, dict):
        raise GrocyError(f"Expected product stock details for {product_id}, got {type(data).__name__}")
    return data


def product_stock_entries(product_id: int) -> list[dict[str, Any]]:
    data = _request("GET", f"/stock/products/{product_id}/entries")
    return data if isinstance(data, list) else []


def product_by_barcode(barcode: str) -> dict[str, Any]:
    data = _request("GET", f"/stock/products/by-barcode/{barcode}")
    if not isinstance(data, dict):
        raise GrocyError(f"Expected barcode lookup object for {barcode}, got {type(data).__name__}")
    return data


def add_stock(product_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    data = _request("POST", f"/stock/products/{product_id}/add", json=payload)
    return data if isinstance(data, dict) else {"ok": True, "response": data}


def consume_stock(product_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    data = _request("POST", f"/stock/products/{product_id}/consume", json=payload)
    return data if isinstance(data, dict) else {"ok": True, "response": data}


def inventory_product(product_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    data = _request("POST", f"/stock/products/{product_id}/inventory", json=payload)
    return data if isinstance(data, dict) else {"ok": True, "response": data}


def add_to_shopping_list(payload: dict[str, Any]) -> dict[str, Any]:
    data = _request("POST", "/stock/shoppinglist/add-product", json=payload)
    return data if isinstance(data, dict) else {"ok": True, "response": data}


def remove_from_shopping_list(payload: dict[str, Any]) -> dict[str, Any]:
    data = _request("POST", "/stock/shoppinglist/remove-product", json=payload)
    return data if isinstance(data, dict) else {"ok": True, "response": data}
