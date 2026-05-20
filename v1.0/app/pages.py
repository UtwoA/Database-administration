from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import Settings, get_settings
from app.db import get_database
from app.repositories import ShopRepository
from app.security import ROLE_PERMISSIONS


router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="templates")


def get_repository(settings: Settings = Depends(get_settings)) -> ShopRepository:
    return ShopRepository(get_database(), settings)


def can(role: str, permission: str) -> bool:
    permissions = ROLE_PERMISSIONS.get(role, set())
    return "*" in permissions or permission in permissions


def role_or_default(role: str | None) -> str:
    if role in ROLE_PERMISSIONS:
        return role
    return "guest"


def page_url(path: str, **params: Any) -> str:
    clean = {key: value for key, value in params.items() if value not in (None, "")}
    if not clean:
        return path
    return f"{path}?{urlencode(clean)}"


def render(request: Request, template: str, context: dict[str, Any]):
    role = role_or_default(context.get("role"))
    base_context = {
        "request": request,
        "role": role,
        "roles": list(ROLE_PERMISSIONS.keys()),
        "client_id": context.get("client_id") or "",
        "can": can,
        "message": context.get("message"),
        "error": context.get("error"),
    }
    base_context.update(context)
    return templates.TemplateResponse(template, base_context)


@router.get("/")
def shop_home(
    request: Request,
    role: str = "guest",
    client_id: str = "",
    category_id: str | None = None,
    q: str | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    manufacturer: str | None = None,
    technology: str | None = None,
    paper_format: str | None = None,
    message: str | None = None,
    error: str | None = None,
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    characteristics = {
        key: value
        for key, value in {
            "technology": technology,
            "paper_format": paper_format,
        }.items()
        if value
    }
    return render(
        request,
        "shop.html",
        {
            "role": role,
            "client_id": client_id,
            "categories": repo.list_categories(),
            "products": repo.list_products(category_id, q, min_price, max_price, manufacturer, characteristics),
            "filters": {
                "category_id": category_id or "",
                "q": q or "",
                "min_price": min_price if min_price is not None else "",
                "max_price": max_price if max_price is not None else "",
                "manufacturer": manufacturer or "",
                "technology": technology or "",
                "paper_format": paper_format or "",
            },
            "message": message,
            "error": error,
        },
    )


@router.post("/cart/items")
def add_cart_item_page(
    request: Request,
    product_id: str = Form(...),
    quantity: int = Form(1),
    client_id: str = Form(...),
    role: str = Form("user"),
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    if not can(role, "manage_own_cart"):
        return RedirectResponse(page_url("/", role=role, client_id=client_id, error="forbidden"), status_code=303)
    try:
        repo.add_cart_item(client_id, product_id, quantity)
    except HTTPException as exc:
        return RedirectResponse(page_url("/", role=role, client_id=client_id, error=exc.detail), status_code=303)
    return RedirectResponse(page_url("/cart", role=role, client_id=client_id, message="added"), status_code=303)


@router.get("/cart")
def cart_page(
    request: Request,
    role: str = "user",
    client_id: str = "",
    message: str | None = None,
    error: str | None = None,
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    cart = {"items": [], "total": 0}
    if client_id and can(role, "manage_own_cart"):
        try:
            cart = repo.get_cart(client_id)
        except HTTPException as exc:
            error = str(exc.detail)
    return render(request, "cart.html", {"role": role, "client_id": client_id, "cart": cart, "message": message, "error": error})


@router.post("/orders/create")
def create_order_page(
    client_id: str = Form(...),
    role: str = Form("user"),
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    if not can(role, "create_order"):
        return RedirectResponse(page_url("/cart", role=role, client_id=client_id, error="forbidden"), status_code=303)
    try:
        repo.create_order_from_cart(client_id)
    except HTTPException as exc:
        return RedirectResponse(page_url("/cart", role=role, client_id=client_id, error=exc.detail), status_code=303)
    return RedirectResponse(page_url("/orders", role=role, client_id=client_id, message="created"), status_code=303)


@router.get("/orders")
def orders_page(
    request: Request,
    role: str = "user",
    client_id: str = "",
    message: str | None = None,
    error: str | None = None,
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    orders = []
    if client_id and can(role, "read_own_orders"):
        try:
            orders = repo.list_client_orders(client_id)
        except HTTPException as exc:
            error = str(exc.detail)
    return render(request, "orders.html", {"role": role, "client_id": client_id, "orders": orders, "message": message, "error": error})


@router.get("/manager/products")
def manager_products_page(
    request: Request,
    role: str = "manager",
    client_id: str = "",
    message: str | None = None,
    error: str | None = None,
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    products = repo.list_products() if can(role, "manage_products") else []
    categories = repo.list_categories() if can(role, "manage_products") else []
    return render(
        request,
        "manager_products.html",
        {"role": role, "client_id": client_id, "products": products, "categories": categories, "message": message, "error": error},
    )


@router.post("/manager/products")
def create_product_page(
    role: str = Form("manager"),
    client_id: str = Form(""),
    name: str = Form(...),
    category_id: str = Form(...),
    price: float = Form(...),
    quantity: int = Form(...),
    manufacturer: str = Form(""),
    technology: str = Form(""),
    paper_format: str = Form(""),
    print_speed: str = Form(""),
    resolution: str = Form(""),
    colors_number: str = Form(""),
    tray_capacity: str = Form(""),
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    if not can(role, "manage_products"):
        return RedirectResponse(page_url("/manager/products", role=role, client_id=client_id, error="forbidden"), status_code=303)
    characteristics = {
        key: value
        for key, value in {
            "technology": technology,
            "paper_format": paper_format,
            "print_speed": print_speed,
            "resolution": resolution,
            "colors_number": colors_number,
            "tray_capacity": tray_capacity,
        }.items()
        if value
    }
    repo.create_product(
        {
            "name": name,
            "category_id": category_id,
            "price": price,
            "quantity": quantity,
            "manufacturer": manufacturer,
            "characteristics": characteristics,
        }
    )
    return RedirectResponse(page_url("/manager/products", role=role, client_id=client_id, message="product-created"), status_code=303)


@router.post("/manager/products/{product_id}/delete")
def delete_product_page(
    product_id: str,
    role: str = Form("manager"),
    client_id: str = Form(""),
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    if can(role, "manage_products"):
        repo.delete_product(product_id)
    return RedirectResponse(page_url("/manager/products", role=role, client_id=client_id), status_code=303)


@router.post("/manager/orders/{order_id}/status")
def update_order_status_page(
    order_id: str,
    status: str = Form(...),
    role: str = Form("manager"),
    client_id: str = Form(""),
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    if can(role, "update_order_status"):
        repo.update_order_status(order_id, status)
    return RedirectResponse(page_url("/manager/analytics", role=role, client_id=client_id), status_code=303)


@router.get("/manager/analytics")
def manager_analytics_page(
    request: Request,
    role: str = "manager",
    client_id: str = "",
    months: int = 3,
    min_orders: int = 2,
    from_date: date = date.today() - timedelta(days=90),
    to_date: date = date.today(),
    target_date: date = date.today(),
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    analytics = {"top_sales": [], "active_clients": [], "categories_demand": [], "unsold_products": [], "orders": []}
    if can(role, "read_analytics"):
        analytics = {
            "top_sales": repo.top_sales(months, 10),
            "active_clients": repo.active_clients(min_orders, from_date),
            "categories_demand": repo.categories_demand(from_date, to_date),
            "unsold_products": repo.unsold_products(target_date),
            "orders": repo.list_orders(30),
        }
    return render(
        request,
        "manager_analytics.html",
        {
            "role": role,
            "client_id": client_id,
            "analytics": analytics,
            "filters": {
                "months": months,
                "min_orders": min_orders,
                "from_date": from_date,
                "to_date": to_date,
                "target_date": target_date,
            },
        },
    )
