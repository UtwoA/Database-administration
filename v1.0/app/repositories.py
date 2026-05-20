from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from pymongo.database import Database

from app.config import Settings
from app.schema_adapter import SchemaAdapter, date_end, date_start, id_filter, parse_id, parse_object_id


ORDER_STATUSES = {"processing", "shipped", "delivered", "cancelled"}


class ShopRepository:
    def __init__(self, db: Database, settings: Settings):
        self.db = db
        self.settings = settings
        self.adapter = SchemaAdapter(settings)

    @property
    def products(self):
        return self.db[self.settings.products_collection]

    @property
    def categories(self):
        return self.db[self.settings.categories_collection]

    @property
    def clients(self):
        return self.db[self.settings.clients_collection]

    @property
    def orders(self):
        return self.db[self.settings.orders_collection]

    @property
    def carts(self):
        return self.db[self.settings.carts_collection]

    def list_categories(self) -> list[dict[str, Any]]:
        return [self.adapter.category_to_api(doc) for doc in self.categories.find({})]

    def list_clients(self) -> list[dict[str, Any]]:
        cursor = self.clients.find({}).sort(
            [
                (self.settings.client_last_name_field, 1),
                (self.settings.client_name_field, 1),
            ]
        )
        return [self.adapter.client_to_api(doc) for doc in cursor]

    def list_products(
        self,
        category_id: str | None = None,
        q: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        manufacturer: str | None = None,
        characteristics: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        s = self.settings
        query: dict[str, Any] = {}

        if category_id:
            query[s.product_category_field] = {"$in": [parse_id(category_id), category_id]}
        if q:
            query[s.product_name_field] = {"$regex": q, "$options": "i"}
        if min_price is not None or max_price is not None:
            query[s.product_price_field] = {}
            if min_price is not None:
                query[s.product_price_field]["$gte"] = min_price
            if max_price is not None:
                query[s.product_price_field]["$lte"] = max_price
        if manufacturer:
            query[s.product_manufacturer_field] = {"$regex": manufacturer, "$options": "i"}

        for key, value in (characteristics or {}).items():
            if key == "technology":
                query[s.product_technology_field] = {"$regex": value, "$options": "i"}
            elif key == "paper_format":
                query[s.product_paper_format_field] = {"$regex": value, "$options": "i"}
            else:
                query[f"{s.product_characteristics_field}.{key}"] = {"$regex": value, "$options": "i"}

        cursor = self.products.find(query).sort(s.product_name_field, 1)
        return [self.adapter.product_to_api(doc) for doc in cursor]

    def get_product(self, product_id: str) -> dict[str, Any]:
        doc = self.products.find_one(id_filter(product_id))
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        return self.adapter.product_to_api(doc)

    def create_product(self, payload: dict[str, Any]) -> dict[str, Any]:
        doc = self.adapter.product_to_db(payload)
        result = self.products.insert_one(doc)
        created = self.products.find_one({"_id": result.inserted_id})
        return self.adapter.product_to_api(created)

    def update_product(self, product_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        update = self.adapter.product_to_db(payload)
        if not update:
            return self.get_product(product_id)
        result = self.products.update_one(id_filter(product_id), {"$set": update})
        if result.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        return self.get_product(product_id)

    def delete_product(self, product_id: str) -> dict[str, str]:
        result = self.products.delete_one(id_filter(product_id))
        if result.deleted_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        return {"status": "deleted", "product_id": product_id}

    def get_client(self, client_id: str) -> dict[str, Any]:
        doc = self.get_client_doc(client_id)
        return self.adapter.client_to_api(doc)

    def create_client(self, payload: dict[str, Any]) -> dict[str, Any]:
        doc = self.adapter.client_to_db(payload)
        result = self.clients.insert_one(doc)
        client_id = str(result.inserted_id)
        self._get_or_create_cart_doc(client_id)
        return self.get_client(client_id)

    def update_client(self, client_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        update = {
            key: value
            for key, value in self.adapter.client_to_db(payload).items()
            if value is not None
        }
        if not update:
            return self.get_client(client_id)
        result = self.clients.update_one(id_filter(client_id), {"$set": update})
        if result.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
        return self.get_client(client_id)

    def delete_client(self, client_id: str) -> dict[str, str]:
        client = self.get_client_doc(client_id)
        customer_id = parse_id(client_id)
        self.carts.delete_many({"customerId": customer_id})
        self.orders.delete_many({self.settings.order_customer_field: {"$in": [customer_id, client_id]}})
        self.clients.delete_one({"_id": client["_id"]})
        return {"status": "deleted", "client_id": client_id}

    def get_client_doc(self, client_id: str) -> dict[str, Any]:
        doc = self.clients.find_one(id_filter(client_id))
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
        return doc

    def add_cart_item(self, client_id: str, product_id: str, quantity: int) -> dict[str, Any]:
        if quantity <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be positive.")

        self.get_client_doc(client_id)
        product = self.get_product(product_id)

        cart = self._get_or_create_cart_doc(client_id)
        items = cart.get("products") or []
        item = next((x for x in items if str(x.get("productId")) == product["id"] or str(x.get("product_id")) == product["id"]), None)
        existing_quantity = int(item.get("quantity", 0)) if item else 0
        requested_quantity = existing_quantity + quantity
        if product["quantity"] < requested_quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough product in stock.")

        if item:
            item["quantity"] = requested_quantity
            item["price"] = product["price"]
            item["name"] = product["name"]
        else:
            items.append(
                {
                    "productId": parse_id(product["id"]),
                    "name": product["name"],
                    "price": product["price"],
                    "quantity": quantity,
                }
            )

        self.carts.update_one({"_id": cart["_id"]}, {"$set": {"products": items}})
        return self.get_cart(client_id)

    def get_cart(self, client_id: str) -> dict[str, Any]:
        self.get_client_doc(client_id)
        cart = self._get_or_create_cart_doc(client_id)
        items = cart.get("products") or []
        normalized_items = []
        total = 0.0
        for item in items:
            price = float(item.get("price", 0))
            quantity = int(item.get("quantity", 0))
            total += price * quantity
            product_id = str(item.get("productId", item.get("product_id")))
            product = self.products.find_one(id_filter(product_id))
            api_product = self.adapter.product_to_api(product) if product else {}
            normalized_items.append(
                {
                    "product_id": product_id,
                    "name": item.get("name"),
                    "category_id": api_product.get("category_id"),
                    "price": price,
                    "quantity": quantity,
                    "subtotal": price * quantity,
                }
            )
        return {"client_id": client_id, "items": normalized_items, "total": total}

    def create_order_from_cart(self, client_id: str) -> dict[str, Any]:
        cart = self.get_cart(client_id)
        if not cart["items"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty.")

        now = datetime.now(timezone.utc)
        employee_id = parse_object_id(self.settings.default_employee_id)
        products = [
            {
                "productId": parse_id(str(item["product_id"])),
                "name": item["name"],
                "quantity": int(item["quantity"]),
                "price": float(item["price"]),
            }
            for item in cart["items"]
        ]
        order = {
            self.settings.order_customer_field: parse_id(client_id),
            self.settings.order_employee_field: employee_id,
            self.settings.order_products_field: products,
            self.settings.order_total_field: cart["total"],
            self.settings.order_status_field: "processing",
            self.settings.order_delivery_address_field: self.settings.default_delivery_address,
            self.settings.order_date_field: now,
            "updated_at": now,
        }
        if self.settings.order_employee_required_field != self.settings.order_employee_field:
            order[self.settings.order_employee_required_field] = employee_id
        result = self.orders.insert_one(order)

        for item in cart["items"]:
            product_doc = self.products.find_one(id_filter(str(item["product_id"])))
            if product_doc and self.settings.product_quantity_field in product_doc:
                self.products.update_one(
                    id_filter(str(item["product_id"])),
                    {"$inc": {self.settings.product_quantity_field: -item["quantity"]}},
                )

        self.carts.update_one({"customerId": parse_id(client_id)}, {"$set": {"products": []}})
        created = self.orders.find_one({"_id": result.inserted_id})
        return self.adapter.order_to_api(created)

    def list_client_orders(self, client_id: str) -> list[dict[str, Any]]:
        field = self.settings.order_customer_field
        query = {field: {"$in": [parse_id(client_id), client_id]}}
        return [self.adapter.order_to_api(doc) for doc in self.orders.find(query).sort(self.settings.order_date_field, -1)]

    def list_orders(self, limit: int = 50) -> list[dict[str, Any]]:
        return [self.adapter.order_to_api(doc) for doc in self.orders.find({}).sort(self.settings.order_date_field, -1).limit(limit)]

    def update_order_status(self, order_id: str, new_status: str) -> dict[str, Any]:
        if new_status not in ORDER_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order status.")
        result = self.orders.update_one(
            id_filter(order_id),
            {"$set": {self.settings.order_status_field: new_status, "updated_at": datetime.now(timezone.utc)}},
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
        doc = self.orders.find_one(id_filter(order_id))
        return self.adapter.order_to_api(doc)

    def top_sales(self, months: int, limit: int) -> list[dict[str, Any]]:
        since = datetime.now(timezone.utc) - timedelta(days=30 * months)
        pipeline = [
            {"$match": {self.settings.order_date_field: {"$gte": since}}},
            {"$unwind": f"${self.settings.order_products_field}"},
            {
                "$group": {
                    "_id": f"${self.settings.order_products_field}.productId",
                    "name": {"$first": f"${self.settings.order_products_field}.name"},
                    "quantity_sold": {"$sum": f"${self.settings.order_products_field}.quantity"},
                    "revenue": {
                        "$sum": {
                            "$multiply": [
                                f"${self.settings.order_products_field}.price",
                                f"${self.settings.order_products_field}.quantity",
                            ]
                        }
                    },
                }
            },
            {"$sort": {"revenue": -1, "quantity_sold": -1}},
            {"$limit": limit},
        ]
        return [{"product_id": str(doc.pop("_id")), **doc} for doc in self.orders.aggregate(pipeline)]

    def active_clients(self, min_orders: int, since_date: date) -> list[dict[str, Any]]:
        pipeline = [
            {"$match": {self.settings.order_date_field: {"$gte": date_start(since_date)}}},
            {
                "$group": {
                    "_id": f"${self.settings.order_customer_field}",
                    "orders_count": {"$sum": 1},
                    "total_spent": {"$sum": f"${self.settings.order_total_field}"},
                }
            },
            {"$match": {"orders_count": {"$gt": min_orders}}},
            {"$sort": {"orders_count": -1, "total_spent": -1}},
        ]
        return [{"client_id": str(doc.pop("_id")), **doc} for doc in self.orders.aggregate(pipeline)]

    def categories_demand(self, from_date: date, to_date: date) -> list[dict[str, Any]]:
        pipeline = [
            {"$match": {self.settings.order_date_field: {"$gte": date_start(from_date), "$lte": date_end(to_date)}}},
            {"$unwind": f"${self.settings.order_products_field}"},
            {
                "$lookup": {
                    "from": self.settings.products_collection,
                    "localField": f"{self.settings.order_products_field}.productId",
                    "foreignField": "_id",
                    "as": "product_doc",
                }
            },
            {"$unwind": {"path": "$product_doc", "preserveNullAndEmptyArrays": True}},
            {
                "$group": {
                    "_id": f"$product_doc.{self.settings.product_category_field}",
                    "quantity_sold": {"$sum": f"${self.settings.order_products_field}.quantity"},
                    "revenue": {
                        "$sum": {
                            "$multiply": [
                                f"${self.settings.order_products_field}.price",
                                f"${self.settings.order_products_field}.quantity",
                            ]
                        }
                    },
                }
            },
            {
                "$lookup": {
                    "from": self.settings.categories_collection,
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "category_doc",
                }
            },
            {"$unwind": {"path": "$category_doc", "preserveNullAndEmptyArrays": True}},
            {"$sort": {"quantity_sold": -1, "revenue": -1}},
        ]
        return [
            {
                "category_id": str(doc.pop("_id")),
                "category_name": (doc.get("category_doc") or {}).get(self.settings.category_name_field),
                "quantity_sold": doc["quantity_sold"],
                "revenue": doc["revenue"],
            }
            for doc in self.orders.aggregate(pipeline)
        ]

    def unsold_products(self, target_date: date) -> list[dict[str, Any]]:
        sold_ids = self.orders.distinct(
            f"{self.settings.order_products_field}.productId",
            {self.settings.order_date_field: {"$gte": date_start(target_date), "$lte": date_end(target_date)}},
        )
        sold_as_strings = [str(value) for value in sold_ids]
        products = self.list_products()
        return [product for product in products if product["id"] not in sold_as_strings]

    def _get_or_create_cart_doc(self, client_id: str) -> dict[str, Any]:
        customer_id = parse_id(client_id)
        cart = self.carts.find_one({"customerId": customer_id})
        if cart:
            return cart
        result = self.carts.insert_one({"customerId": customer_id, "products": []})
        return self.carts.find_one({"_id": result.inserted_id})
