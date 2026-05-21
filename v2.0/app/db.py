from contextlib import contextmanager
from typing import Iterator

from psycopg import connect
from psycopg.rows import dict_row
from pymongo import MongoClient
from pymongo.database import Database

from app.config import Settings, get_settings


_mongo_client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    global _mongo_client
    if _mongo_client is None:
        settings = get_settings()
        _mongo_client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=3000)
    return _mongo_client


def get_mongo_database() -> Database:
    settings = get_settings()
    return get_mongo_client()[settings.mongo_db_name]


@contextmanager
def postgres_connection(settings: Settings | None = None) -> Iterator:
    active_settings = settings or get_settings()
    connection = connect(active_settings.postgres_dsn, row_factory=dict_row, connect_timeout=3)
    try:
        yield connection
    finally:
        connection.close()


def ping_mongodb() -> None:
    get_mongo_client().admin.command("ping")


def ping_postgresql(settings: Settings | None = None) -> None:
    with postgres_connection(settings) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()


def get_health_status(settings: Settings | None = None) -> dict[str, object]:
    active_settings = settings or get_settings()
    databases: dict[str, dict[str, str]] = {}

    try:
        ping_mongodb()
        databases["mongodb"] = {"status": "connected"}
    except Exception as exc:  # pragma: no cover - surfaced in /health
        databases["mongodb"] = {"status": "error", "error": str(exc)}

    try:
        ping_postgresql(active_settings)
        databases["postgresql"] = {"status": "connected"}
    except Exception as exc:  # pragma: no cover - surfaced in /health
        databases["postgresql"] = {"status": "error", "error": str(exc)}

    overall_status = "ok" if all(item["status"] == "connected" for item in databases.values()) else "degraded"
    return {
        "status": overall_status,
        "application": {
            "name": active_settings.app_name,
            "version": active_settings.app_version,
        },
        "databases": databases,
    }
