from pymongo import MongoClient
from pymongo.database import Database

from app.config import get_settings


_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=3000)
    return _client


def get_database() -> Database:
    settings = get_settings()
    return get_client()[settings.mongo_db_name]


def ping_database() -> bool:
    get_client().admin.command("ping")
    return True
