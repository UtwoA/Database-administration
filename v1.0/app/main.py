from datetime import date
from typing import Annotated
from typing import Any
from typing import Literal

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pymongo.errors import PyMongoError
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.db import get_database, ping_database
from app.pages import router as pages_router
from app.repositories import ShopRepository
from app.security import require_permission


app = FastAPI(
    title="Printer Shop API",
    description="FastAPI layer over MongoDB for printer shop practical work.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(pages_router)
templates = Jinja2Templates(directory="templates")


@app.exception_handler(PyMongoError)
def mongo_exception_handler(request: Request, exc: PyMongoError):
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            "db_error.html",
            {"request": request, "error": str(exc)},
            status_code=503,
        )
    return JSONResponse(status_code=503, content={"detail": "MongoDB is unavailable.", "error": str(exc)})


class CartItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)


class OrderStatusUpdate(BaseModel):
    status: Literal["processing", "shipped", "delivered", "cancelled"]


class ProductCreate(BaseModel):
    name: str = Field(min_length=2)
    category_id: str
    price: float = Field(ge=0)
    quantity: int = Field(ge=0)
    manufacturer: str | None = None
    characteristics: dict[str, Any] = Field(default_factory=dict)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2)
    category_id: str | None = None
    price: float | None = Field(default=None, ge=0)
    quantity: int | None = Field(default=None, ge=0)
    manufacturer: str | None = None
    characteristics: dict[str, Any] | None = None


def get_repository(settings: Settings = Depends(get_settings)) -> ShopRepository:
    return ShopRepository(get_database(), settings)


@app.get("/health")
def health() -> dict[str, object]:
    ping_database()
    return {"status": "ok", "database": "connected"}


@app.get("/categories", dependencies=[Depends(require_permission("read_products"))])
def list_categories(repo: ShopRepository = Depends(get_repository)):
    return repo.list_categories()


@app.get("/products", dependencies=[Depends(require_permission("read_products"))])
def list_products(
    request: Request,
    category_id: str | None = None,
    q: str | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    manufacturer: str | None = None,
    repo: ShopRepository = Depends(get_repository),
):
    known = {"category_id", "q", "min_price", "max_price", "manufacturer"}
    characteristics = {key: value for key, value in request.query_params.items() if key not in known}
    return repo.list_products(category_id, q, min_price, max_price, manufacturer, characteristics)


@app.get("/products/{product_id}", dependencies=[Depends(require_permission("read_products"))])
def get_product(product_id: str, repo: ShopRepository = Depends(get_repository)):
    return repo.get_product(product_id)


@app.post("/products", dependencies=[Depends(require_permission("manage_products"))])
def create_product(payload: ProductCreate, repo: ShopRepository = Depends(get_repository)):
    return repo.create_product(payload.model_dump())


@app.patch("/products/{product_id}", dependencies=[Depends(require_permission("manage_products"))])
def update_product(product_id: str, payload: ProductUpdate, repo: ShopRepository = Depends(get_repository)):
    return repo.update_product(product_id, payload.model_dump(exclude_unset=True))


@app.delete("/products/{product_id}", dependencies=[Depends(require_permission("manage_products"))])
def delete_product(product_id: str, repo: ShopRepository = Depends(get_repository)):
    return repo.delete_product(product_id)


@app.post("/clients/{client_id}/cart/items", dependencies=[Depends(require_permission("manage_own_cart"))])
def add_cart_item(client_id: str, payload: CartItemCreate, repo: ShopRepository = Depends(get_repository)):
    return repo.add_cart_item(client_id, payload.product_id, payload.quantity)


@app.get("/clients/{client_id}/cart", dependencies=[Depends(require_permission("manage_own_cart"))])
def get_cart(client_id: str, repo: ShopRepository = Depends(get_repository)):
    return repo.get_cart(client_id)


@app.post("/clients/{client_id}/orders", dependencies=[Depends(require_permission("create_order"))])
def create_order(client_id: str, repo: ShopRepository = Depends(get_repository)):
    return repo.create_order_from_cart(client_id)


@app.get("/clients/{client_id}/orders", dependencies=[Depends(require_permission("read_own_orders"))])
def list_client_orders(client_id: str, repo: ShopRepository = Depends(get_repository)):
    return repo.list_client_orders(client_id)


@app.patch("/orders/{order_id}/status", dependencies=[Depends(require_permission("update_order_status"))])
def update_order_status(order_id: str, payload: OrderStatusUpdate, repo: ShopRepository = Depends(get_repository)):
    return repo.update_order_status(order_id, payload.status)


@app.get("/analytics/top-sales", dependencies=[Depends(require_permission("read_analytics"))])
def top_sales(
    months: Annotated[int, Query(ge=1, le=36)] = 3,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    repo: ShopRepository = Depends(get_repository),
):
    return repo.top_sales(months, limit)


@app.get("/analytics/active-clients", dependencies=[Depends(require_permission("read_analytics"))])
def active_clients(
    min_orders: Annotated[int, Query(ge=0)] = 2,
    since: date = Query(...),
    repo: ShopRepository = Depends(get_repository),
):
    return repo.active_clients(min_orders, since)


@app.get("/analytics/categories-demand", dependencies=[Depends(require_permission("read_analytics"))])
def categories_demand(
    from_date: date = Query(...),
    to_date: date = Query(...),
    repo: ShopRepository = Depends(get_repository),
):
    return repo.categories_demand(from_date, to_date)


@app.get("/analytics/unsold-products", dependencies=[Depends(require_permission("read_analytics"))])
def unsold_products(
    target_date: date = Query(...),
    repo: ShopRepository = Depends(get_repository),
):
    return repo.unsold_products(target_date)
