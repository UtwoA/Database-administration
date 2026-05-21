from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv


ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH, override=True)


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


class Settings:
    app_name: str = _env("APP_NAME", "Гибридный стенд магазина")
    app_version: str = _env("APP_VERSION", "2.0.0")

    mongo_uri: str = _env("MONGO_URI", "mongodb://localhost:27017")
    mongo_db_name: str = _env("MONGO_DB_NAME", "hybrid_store")
    mongo_products_collection: str = _env("MONGO_PRODUCTS_COLLECTION", "products")

    postgres_dsn: str = _env(
        "POSTGRES_DSN",
        "postgresql://store_admin:admin123@localhost:5432/hybrid_store",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
