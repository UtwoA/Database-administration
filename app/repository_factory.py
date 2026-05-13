from app.config import Settings
from app.db import get_database
from app.mock_repository import MockShopRepository
from app.repositories import ShopRepository


_mock_repository = MockShopRepository()


def get_shop_repository(settings: Settings):
    if settings.use_mock_data:
        return _mock_repository
    return ShopRepository(get_database(), settings)
