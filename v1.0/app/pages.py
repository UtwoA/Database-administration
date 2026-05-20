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


router = APIRouter()
templates = Jinja2Templates(directory="templates")

DEMO_CLIENTS = [
    {"id": "665000000000000000000201", "label": "Demo Client", "role": "user"},
    {"id": "665000000000000000000202", "label": "Alice Ivanova", "role": "user"},
    {"id": "665000000000000000000203", "label": "Sofia Petrova", "role": "user"},
]

ROLE_GUIDES = {
    "guest": {
        "title": "Гость",
        "description": "Может просматривать категории и товары без корзины и заказов.",
    },
    "user": {
        "title": "Покупатель",
        "description": "Работает с каталогом, корзиной и собственными заказами через client_id.",
    },
    "manager": {
        "title": "Менеджер",
        "description": "Управляет товарами, меняет статусы заказов и смотрит аналитику.",
    },
    "admin": {
        "title": "Администратор",
        "description": "Имеет полный доступ и управляет клиентами в стенде.",
    },
}

SESSION_PRESETS = [
    {
        "label": "Каталог как гость",
        "path": "/",
        "params": {"role": "guest"},
        "caption": "Просмотр каталога без client_id",
    },
    {
        "label": "Покупатель Demo Client",
        "path": "/",
        "params": {"role": "user", "client_id": "665000000000000000000201"},
        "caption": "Корзина и заказы тестового клиента",
    },
    {
        "label": "Менеджер",
        "path": "/manager/products",
        "params": {"role": "manager"},
        "caption": "Товары, статусы заказов и аналитика",
    },
    {
        "label": "Администратор",
        "path": "/admin/clients",
        "params": {"role": "admin"},
        "caption": "Управление клиентами и полный доступ",
    },
]


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


def app_url(root_path: str, path: str, **params: Any) -> str:
    return f"{root_path}{page_url(path, **params)}"


def make_app_path(root_path: str):
    def helper(path: str, **params: Any) -> str:
        return app_url(root_path, path, **params)

    return helper


def redirect_to(request: Request, path: str, status_code: int = 303, **params: Any) -> RedirectResponse:
    return RedirectResponse(app_url(request.scope.get("root_path", ""), path, **params), status_code=status_code)


def forbidden_redirect(request: Request, role: str, client_id: str = "") -> RedirectResponse:
    return redirect_to(request, "/", role=role, client_id=client_id, error="forbidden")


def require_page_permission(request: Request, role: str, permission: str, client_id: str = "") -> RedirectResponse | None:
    if can(role, permission):
        return None
    return forbidden_redirect(request, role, client_id)


def render(request: Request, template: str, context: dict[str, Any]):
    role = role_or_default(context.get("role"))
    root_path = request.scope.get("root_path", "")
    app_path = make_app_path(root_path)
    base_context = {
        "request": request,
        "role": role,
        "roles": list(ROLE_PERMISSIONS.keys()),
        "role_guide": ROLE_GUIDES[role],
        "session_presets": [
            {**preset, "href": app_path(preset["path"], **preset["params"])}
            for preset in SESSION_PRESETS
        ],
        "demo_clients": DEMO_CLIENTS,
        "client_id": context.get("client_id") or "",
        "can": can,
        "app_path": app_path,
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
        return redirect_to(request, "/", role=role, client_id=client_id, error="forbidden")
    try:
        repo.add_cart_item(client_id, product_id, quantity)
    except HTTPException as exc:
        return redirect_to(request, "/", role=role, client_id=client_id, error=exc.detail)
    return redirect_to(request, "/cart", role=role, client_id=client_id, message="added")


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
    redirect = require_page_permission(request, role, "manage_own_cart", client_id)
    if redirect:
        return redirect
    cart = {"items": [], "total": 0}
    if client_id:
        try:
            cart = repo.get_cart(client_id)
        except HTTPException as exc:
            error = str(exc.detail)
    return render(request, "cart.html", {"role": role, "client_id": client_id, "cart": cart, "message": message, "error": error})


@router.post("/orders/create")
def create_order_page(
    request: Request,
    client_id: str = Form(...),
    role: str = Form("user"),
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    if not can(role, "create_order"):
        return redirect_to(request, "/cart", role=role, client_id=client_id, error="forbidden")
    try:
        repo.create_order_from_cart(client_id)
    except HTTPException as exc:
        return redirect_to(request, "/cart", role=role, client_id=client_id, error=exc.detail)
    return redirect_to(request, "/orders", role=role, client_id=client_id, message="created")


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
    redirect = require_page_permission(request, role, "read_own_orders", client_id)
    if redirect:
        return redirect
    orders = []
    if client_id:
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
    redirect = require_page_permission(request, role, "manage_products", client_id)
    if redirect:
        return redirect
    products = repo.list_products()
    categories = repo.list_categories()
    return render(
        request,
        "manager_products.html",
        {"role": role, "client_id": client_id, "products": products, "categories": categories, "message": message, "error": error},
    )


@router.post("/manager/products")
def create_product_page(
    request: Request,
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
        return redirect_to(request, "/manager/products", role=role, client_id=client_id, error="forbidden")
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
    return redirect_to(request, "/manager/products", role=role, client_id=client_id, message="product-created")


@router.post("/manager/products/{product_id}/delete")
def delete_product_page(
    request: Request,
    product_id: str,
    role: str = Form("manager"),
    client_id: str = Form(""),
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    if not can(role, "manage_products"):
        return forbidden_redirect(request, role, client_id)
    repo.delete_product(product_id)
    return redirect_to(request, "/manager/products", role=role, client_id=client_id)


@router.post("/manager/orders/{order_id}/status")
def update_order_status_page(
    request: Request,
    order_id: str,
    status: str = Form(...),
    role: str = Form("manager"),
    client_id: str = Form(""),
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    if not can(role, "update_order_status"):
        return forbidden_redirect(request, role, client_id)
    repo.update_order_status(order_id, status)
    return redirect_to(request, "/manager/analytics", role=role, client_id=client_id)


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
    redirect = require_page_permission(request, role, "read_analytics", client_id)
    if redirect:
        return redirect
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


@router.get("/admin/clients")
def admin_clients_page(
    request: Request,
    role: str = "admin",
    client_id: str = "",
    message: str | None = None,
    error: str | None = None,
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    redirect = require_page_permission(request, role, "manage_users", client_id)
    if redirect:
        return redirect
    return render(
        request,
        "admin_clients.html",
        {
            "role": role,
            "client_id": client_id,
            "clients": repo.list_clients(),
            "message": message,
            "error": error,
        },
    )


@router.post("/admin/clients")
def create_client_page(
    request: Request,
    role: str = Form("admin"),
    client_id: str = Form(""),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    if not can(role, "manage_users"):
        return forbidden_redirect(request, role, client_id)
    repo.create_client(
        {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
        }
    )
    return redirect_to(request, "/admin/clients", role=role, client_id=client_id, message="client-created")


@router.post("/admin/clients/{managed_client_id}/edit")
def update_client_page(
    request: Request,
    managed_client_id: str,
    role: str = Form("admin"),
    client_id: str = Form(""),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    if not can(role, "manage_users"):
        return forbidden_redirect(request, role, client_id)
    repo.update_client(
        managed_client_id,
        {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
        },
    )
    return redirect_to(request, "/admin/clients", role=role, client_id=client_id, message="client-updated")


@router.post("/admin/clients/{managed_client_id}/delete")
def delete_client_page(
    request: Request,
    managed_client_id: str,
    role: str = Form("admin"),
    client_id: str = Form(""),
    repo: ShopRepository = Depends(get_repository),
):
    role = role_or_default(role)
    if not can(role, "manage_users"):
        return forbidden_redirect(request, role, client_id)
    repo.delete_client(managed_client_id)
    return redirect_to(request, "/admin/clients", role=role, client_id=client_id, message="client-deleted")
