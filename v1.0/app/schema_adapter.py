from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any

from bson import ObjectId

from app.config import Settings


def stringify_id(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def parse_id(value: str) -> ObjectId | str:
    if ObjectId.is_valid(value):
        return ObjectId(value)
    return value


def parse_object_id(value: str | None) -> ObjectId:
    if value and ObjectId.is_valid(value):
        return ObjectId(value)
    return ObjectId()


def id_filter(value: str, field: str = "_id") -> dict[str, Any]:
    parsed = parse_id(value)
    candidates: list[dict[str, Any]] = [{field: parsed}, {field: value}]
    if field == "_id":
        candidates.append({"id": value})
    return {"$or": candidates}


def date_start(value: date) -> datetime:
    return datetime.combine(value, time.min).replace(tzinfo=timezone.utc)


def date_end(value: date) -> datetime:
    return datetime.combine(value, time.max).replace(tzinfo=timezone.utc)


class SchemaAdapter:
    def __init__(self, settings: Settings):
        self.settings = settings

    def product_to_api(self, doc: dict[str, Any]) -> dict[str, Any]:
        s = self.settings
        characteristics = doc.get(s.product_characteristics_field) or {}
        if not isinstance(characteristics, dict):
            characteristics = {}
        characteristics = {
            **characteristics,
            "technology": doc.get(s.product_technology_field, characteristics.get("technology")),
            "paper_format": doc.get(s.product_paper_format_field, characteristics.get("paper_format")),
            "colors_number": doc.get(s.product_colors_field, characteristics.get("colors_number")),
        }
        return {
            "id": stringify_id(doc.get("_id", doc.get("id"))),
            "name": doc.get(s.product_name_field),
            "category_id": stringify_id(doc.get(s.product_category_field)),
            "price": float(doc.get(s.product_price_field, 0)),
            "quantity": int(doc.get(s.product_quantity_field, 0)),
            "manufacturer": doc.get(s.product_manufacturer_field),
            "characteristics": characteristics,
        }

    def product_to_db(self, payload: dict[str, Any]) -> dict[str, Any]:
        s = self.settings
        mapping = {
            "name": s.product_name_field,
            "category_id": s.product_category_field,
            "price": s.product_price_field,
            "quantity": s.product_quantity_field,
            "manufacturer": s.product_manufacturer_field,
        }
        doc = {mapping[key]: value for key, value in payload.items() if key in mapping and value is not None}
        if "category_id" in payload and payload["category_id"] is not None:
            doc[s.product_category_field] = parse_id(str(payload["category_id"]))
        characteristics = payload.get("characteristics") or {}
        remaining_characteristics = {
            key: value
            for key, value in characteristics.items()
            if key not in {"technology", "paper_format", "colors_number"} and value not in (None, "")
        }
        if "technology" in characteristics:
            doc[s.product_technology_field] = characteristics["technology"]
        if "paper_format" in characteristics:
            doc[s.product_paper_format_field] = characteristics["paper_format"]
        if "colors_number" in characteristics:
            try:
                doc[s.product_colors_field] = int(characteristics["colors_number"])
            except (TypeError, ValueError):
                doc[s.product_colors_field] = characteristics["colors_number"]
        if remaining_characteristics:
            doc[s.product_characteristics_field] = remaining_characteristics
        return doc

    def category_to_api(self, doc: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": stringify_id(doc.get("_id", doc.get("id"))),
            "name": doc.get(self.settings.category_name_field),
        }

    def client_to_api(self, doc: dict[str, Any]) -> dict[str, Any]:
        first_name = doc.get(self.settings.client_name_field)
        last_name = doc.get(self.settings.client_last_name_field)
        name = " ".join(part for part in [first_name, last_name] if part)
        return {
            "id": stringify_id(doc.get("_id", doc.get("id"))),
            "name": name or doc.get("name"),
            "first_name": first_name,
            "last_name": last_name,
            "email": doc.get(self.settings.client_email_field),
            "phone": doc.get("phone"),
            "cart": doc.get("cart", {"items": []}),
        }

    def client_to_db(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            self.settings.client_name_field: payload.get("first_name"),
            self.settings.client_last_name_field: payload.get("last_name"),
            self.settings.client_email_field: payload.get("email"),
            "phone": payload.get("phone"),
        }

    def order_to_api(self, doc: dict[str, Any]) -> dict[str, Any]:
        s = self.settings
        items = doc.get(s.order_products_field, doc.get("items", []))
        normalized_items = []
        for item in items:
            product_id = item.get("productId", item.get("product_id"))
            price = float(item.get("price", 0))
            quantity = int(item.get("quantity", 0))
            normalized_items.append(
                {
                    "product_id": stringify_id(product_id),
                    "name": item.get("name"),
                    "quantity": quantity,
                    "price": price,
                    "subtotal": price * quantity,
                }
            )
        total = doc.get(s.order_total_field, doc.get("total", 0))
        created_at = doc.get(s.order_date_field, doc.get("created_at"))
        return {
            "id": stringify_id(doc.get("_id", doc.get("id"))),
            "client_id": stringify_id(doc.get(s.order_customer_field, doc.get("client_id"))),
            "items": normalized_items,
            "status": doc.get(s.order_status_field, doc.get("status")),
            "created_at": created_at,
            "updated_at": doc.get("updated_at"),
            "total": float(total),
        }
