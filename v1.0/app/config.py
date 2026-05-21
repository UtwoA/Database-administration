from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv


ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH, override=True)


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


class Settings:
    mongo_uri: str = _env("MONGO_URI", "mongodb://localhost:27017")
    mongo_db_name: str = _env("MONGO_DB_NAME", "shop")

    products_collection: str = _env("PRODUCTS_COLLECTION", "products")
    categories_collection: str = _env("CATEGORIES_COLLECTION", "categories")
    clients_collection: str = _env("CLIENTS_COLLECTION", "customers")
    orders_collection: str = _env("ORDERS_COLLECTION", "orders")
    carts_collection: str = _env("CARTS_COLLECTION", "carts")

    product_name_field: str = _env("PRODUCT_NAME_FIELD", "name")
    product_category_field: str = _env("PRODUCT_CATEGORY_FIELD", "categoryId")
    product_price_field: str = _env("PRODUCT_PRICE_FIELD", "price")
    product_quantity_field: str = _env("PRODUCT_QUANTITY_FIELD", "quantity")
    product_manufacturer_field: str = _env("PRODUCT_MANUFACTURER_FIELD", "manufacturer")
    product_characteristics_field: str = _env("PRODUCT_CHARACTERISTICS_FIELD", "characteristics")
    product_technology_field: str = _env("PRODUCT_TECHNOLOGY_FIELD", "technology")
    product_paper_format_field: str = _env("PRODUCT_PAPER_FORMAT_FIELD", "paperFormat")
    product_colors_field: str = _env("PRODUCT_COLORS_FIELD", "colors")

    category_name_field: str = _env("CATEGORY_NAME_FIELD", "name")

    client_name_field: str = _env("CLIENT_NAME_FIELD", "firstName")
    client_email_field: str = _env("CLIENT_EMAIL_FIELD", "email")
    client_last_name_field: str = _env("CLIENT_LAST_NAME_FIELD", "lastName")

    order_customer_field: str = _env("ORDER_CUSTOMER_FIELD", "customerId")
    order_products_field: str = _env("ORDER_PRODUCTS_FIELD", "products")
    order_total_field: str = _env("ORDER_TOTAL_FIELD", "totalPrice")
    order_status_field: str = _env("ORDER_STATUS_FIELD", "status")
    order_date_field: str = _env("ORDER_DATE_FIELD", "orderDate")
    order_employee_field: str = _env("ORDER_EMPLOYEE_FIELD", "employeeId")
    order_employee_required_field: str = _env("ORDER_EMPLOYEE_REQUIRED_FIELD", "employeeId")
    order_delivery_address_field: str = _env("ORDER_DELIVERY_ADDRESS_FIELD", "deliveryAddress")
    default_employee_id: str = _env("DEFAULT_EMPLOYEE_ID", "")
    default_delivery_address: str = _env("DEFAULT_DELIVERY_ADDRESS", "Moscow, Stromynka st., 20")


@lru_cache
def get_settings() -> Settings:
    return Settings()
