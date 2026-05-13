from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status


class MockShopRepository:
    def __init__(self):
        self.categories = [
            {"id": "laser", "name": "Laser printers"},
            {"id": "inkjet", "name": "Inkjet printers"},
            {"id": "led", "name": "LED printers"},
            {"id": "mfp", "name": "Multifunction printers"},
            {"id": "supplies", "name": "Printer supplies"},
        ]
        self.products = [
            {
                "id": "hp-laserjet-pro-m404dn",
                "name": "HP LaserJet Pro M404dn",
                "category_id": "laser",
                "price": 28990.0,
                "quantity": 12,
                "manufacturer": "HP",
                "characteristics": {
                    "technology": "laser",
                    "paper_format": "A4",
                    "print_speed": "38 ppm",
                    "resolution": "1200x1200",
                    "colors_number": "1",
                    "tray_capacity": "250",
                },
            },
            {
                "id": "canon-pixma-g640",
                "name": "Canon PIXMA G640",
                "category_id": "inkjet",
                "price": 34990.0,
                "quantity": 8,
                "manufacturer": "Canon",
                "characteristics": {
                    "technology": "inkjet",
                    "paper_format": "A4",
                    "print_speed": "10 ppm",
                    "resolution": "4800x1200",
                    "colors_number": "6",
                    "tray_capacity": "100",
                },
            },
            {
                "id": "epson-l805",
                "name": "Epson L805",
                "category_id": "inkjet",
                "price": 41990.0,
                "quantity": 5,
                "manufacturer": "Epson",
                "characteristics": {
                    "technology": "inkjet",
                    "paper_format": "A4",
                    "print_speed": "15 ppm",
                    "resolution": "5760x1440",
                    "colors_number": "6",
                    "tray_capacity": "120",
                },
            },
            {
                "id": "pantum-p2500w",
                "name": "Pantum P2500W",
                "category_id": "laser",
                "price": 12990.0,
                "quantity": 20,
                "manufacturer": "Pantum",
                "characteristics": {
                    "technology": "laser",
                    "paper_format": "A4",
                    "print_speed": "22 ppm",
                    "resolution": "1200x1200",
                    "colors_number": "1",
                    "tray_capacity": "150",
                },
            },
            {
                "id": "brother-hl-l8260cdw",
                "name": "Brother HL-L8260CDW",
                "category_id": "led",
                "price": 53990.0,
                "quantity": 6,
                "manufacturer": "Brother",
                "characteristics": {
                    "technology": "led",
                    "paper_format": "A4",
                    "print_speed": "31 ppm",
                    "resolution": "2400x600",
                    "colors_number": "4",
                    "tray_capacity": "300",
                },
            },
            {
                "id": "xerox-b235",
                "name": "Xerox B235 MFP",
                "category_id": "mfp",
                "price": 36990.0,
                "quantity": 7,
                "manufacturer": "Xerox",
                "characteristics": {
                    "technology": "laser",
                    "paper_format": "A4",
                    "print_speed": "34 ppm",
                    "resolution": "600x600",
                    "colors_number": "1",
                    "tray_capacity": "250",
                },
            },
        ]
        self.clients = {
            "demo-client": {
                "id": "demo-client",
                "name": "Demo Client",
                "email": "client@example.com",
                "cart": {"items": []},
            }
        }
        now = datetime.now(timezone.utc)
        self.orders = [
            {
                "id": "order-1001",
                "client_id": "demo-client",
                "items": [
                    {
                        "product_id": "pantum-p2500w",
                        "name": "Pantum P2500W",
                        "category_id": "laser",
                        "price": 12990.0,
                        "quantity": 2,
                        "subtotal": 25980.0,
                    }
                ],
                "status": "completed",
                "created_at": now - timedelta(days=18),
                "updated_at": now - timedelta(days=17),
                "total": 25980.0,
            },
            {
                "id": "order-1002",
                "client_id": "demo-client",
                "items": [
                    {
                        "product_id": "canon-pixma-g640",
                        "name": "Canon PIXMA G640",
                        "category_id": "inkjet",
                        "price": 34990.0,
                        "quantity": 1,
                        "subtotal": 34990.0,
                    }
                ],
                "status": "shipped",
                "created_at": now - timedelta(days=6),
                "updated_at": now - timedelta(days=5),
                "total": 34990.0,
            },
        ]

    def list_categories(self) -> list[dict[str, Any]]:
        return deepcopy(self.categories)

    def list_products(
        self,
        category_id: str | None = None,
        q: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        manufacturer: str | None = None,
        characteristics: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        products = deepcopy(self.products)
        if category_id:
            products = [item for item in products if item["category_id"] == category_id]
        if q:
            needle = q.lower()
            products = [item for item in products if needle in item["name"].lower()]
        if min_price is not None:
            products = [item for item in products if item["price"] >= min_price]
        if max_price is not None:
            products = [item for item in products if item["price"] <= max_price]
        if manufacturer:
            needle = manufacturer.lower()
            products = [item for item in products if needle in (item["manufacturer"] or "").lower()]
        for key, value in (characteristics or {}).items():
            needle = value.lower()
            products = [item for item in products if needle in str(item["characteristics"].get(key, "")).lower()]
        return products

    def get_product(self, product_id: str) -> dict[str, Any]:
        for product in self.products:
            if product["id"] == product_id:
                return deepcopy(product)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    def create_product(self, payload: dict[str, Any]) -> dict[str, Any]:
        product = {
            "id": payload.get("id") or f"mock-{uuid4().hex[:8]}",
            "name": payload["name"],
            "category_id": payload["category_id"],
            "price": float(payload["price"]),
            "quantity": int(payload["quantity"]),
            "manufacturer": payload.get("manufacturer"),
            "characteristics": payload.get("characteristics") or {},
        }
        self.products.append(product)
        return deepcopy(product)

    def update_product(self, product_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        for product in self.products:
            if product["id"] == product_id:
                product.update({key: value for key, value in payload.items() if value is not None})
                return deepcopy(product)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    def delete_product(self, product_id: str) -> dict[str, str]:
        before = len(self.products)
        self.products = [product for product in self.products if product["id"] != product_id]
        if len(self.products) == before:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        return {"status": "deleted", "product_id": product_id}

    def get_cart(self, client_id: str) -> dict[str, Any]:
        client = self._client(client_id)
        items = deepcopy(client["cart"]["items"])
        total = 0.0
        for item in items:
            item["subtotal"] = float(item["price"]) * int(item["quantity"])
            total += item["subtotal"]
        return {"client_id": client_id, "items": items, "total": total}

    def add_cart_item(self, client_id: str, product_id: str, quantity: int) -> dict[str, Any]:
        product = self.get_product(product_id)
        client = self._client(client_id)
        items = client["cart"]["items"]
        item = next((entry for entry in items if entry["product_id"] == product_id), None)
        if item:
            item["quantity"] += quantity
        else:
            items.append(
                {
                    "product_id": product["id"],
                    "name": product["name"],
                    "category_id": product["category_id"],
                    "price": product["price"],
                    "quantity": quantity,
                }
            )
        return self.get_cart(client_id)

    def create_order_from_cart(self, client_id: str) -> dict[str, Any]:
        cart = self.get_cart(client_id)
        if not cart["items"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty.")
        now = datetime.now(timezone.utc)
        order = {
            "id": f"order-{uuid4().hex[:8]}",
            "client_id": client_id,
            "items": cart["items"],
            "status": "created",
            "created_at": now,
            "updated_at": now,
            "total": cart["total"],
        }
        self.orders.append(order)
        self.clients[client_id]["cart"] = {"items": []}
        return deepcopy(order)

    def list_client_orders(self, client_id: str) -> list[dict[str, Any]]:
        return [deepcopy(order) for order in self.orders if order["client_id"] == client_id]

    def list_orders(self, limit: int = 50) -> list[dict[str, Any]]:
        return [deepcopy(order) for order in sorted(self.orders, key=lambda item: item["created_at"], reverse=True)[:limit]]

    def update_order_status(self, order_id: str, new_status: str) -> dict[str, Any]:
        for order in self.orders:
            if order["id"] == order_id:
                order["status"] = new_status
                order["updated_at"] = datetime.now(timezone.utc)
                return deepcopy(order)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    def top_sales(self, months: int, limit: int) -> list[dict[str, Any]]:
        since = datetime.now(timezone.utc) - timedelta(days=30 * months)
        totals: dict[str, dict[str, Any]] = {}
        for order in self.orders:
            if order["created_at"] < since:
                continue
            for item in order["items"]:
                bucket = totals.setdefault(item["product_id"], {"product_id": item["product_id"], "name": item["name"], "quantity_sold": 0, "revenue": 0.0})
                bucket["quantity_sold"] += item["quantity"]
                bucket["revenue"] += item["price"] * item["quantity"]
        return sorted(totals.values(), key=lambda item: (-item["revenue"], -item["quantity_sold"]))[:limit]

    def active_clients(self, min_orders: int, since_date: date) -> list[dict[str, Any]]:
        start = datetime.combine(since_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        totals: dict[str, dict[str, Any]] = {}
        for order in self.orders:
            if order["created_at"] < start:
                continue
            bucket = totals.setdefault(order["client_id"], {"client_id": order["client_id"], "orders_count": 0, "total_spent": 0.0})
            bucket["orders_count"] += 1
            bucket["total_spent"] += order["total"]
        return [item for item in totals.values() if item["orders_count"] > min_orders]

    def categories_demand(self, from_date: date, to_date: date) -> list[dict[str, Any]]:
        start = datetime.combine(from_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = datetime.combine(to_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        totals: dict[str, dict[str, Any]] = {}
        for order in self.orders:
            if not start <= order["created_at"] <= end:
                continue
            for item in order["items"]:
                bucket = totals.setdefault(item["category_id"], {"category_id": item["category_id"], "quantity_sold": 0, "revenue": 0.0})
                bucket["quantity_sold"] += item["quantity"]
                bucket["revenue"] += item["price"] * item["quantity"]
        return sorted(totals.values(), key=lambda item: (-item["quantity_sold"], -item["revenue"]))

    def unsold_products(self, target_date: date) -> list[dict[str, Any]]:
        sold_ids = {
            item["product_id"]
            for order in self.orders
            if order["created_at"].date() == target_date
            for item in order["items"]
        }
        return [deepcopy(product) for product in self.products if product["id"] not in sold_ids]

    def _client(self, client_id: str) -> dict[str, Any]:
        if not client_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client id is required.")
        if client_id not in self.clients:
            self.clients[client_id] = {"id": client_id, "name": client_id, "email": "", "cart": {"items": []}}
        return self.clients[client_id]
