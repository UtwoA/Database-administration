from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import Settings, get_settings
from app.db import get_health_status, get_mongo_database
from app.repositories import PostgresStoreRepository, ProductRepository


router = APIRouter()
templates = Jinja2Templates(directory="templates")

SUCCESS_MESSAGES = {
    "product-created": "Товар успешно добавлен.",
    "product-deleted": "Товар удалён.",
    "branch-created": "Филиал успешно добавлен.",
    "branch-deleted": "Филиал удалён.",
    "employee-created": "Сотрудник успешно добавлен.",
    "employee-deleted": "Сотрудник удалён.",
}

ERROR_MESSAGES = {
    "Invalid product id.": "Некорректный идентификатор товара.",
    "Product not found.": "Товар не найден.",
    "Branch has linked employees and cannot be removed.": "Нельзя удалить филиал: к нему привязаны сотрудники.",
    "Branch not found.": "Филиал не найден.",
    "Employee with this email already exists.": "Сотрудник с таким email уже существует.",
    "Employee not found.": "Сотрудник не найден.",
}

STATUS_LABELS = {
    "ok": "норма",
    "degraded": "деградация",
    "connected": "подключено",
    "error": "ошибка",
}


def get_product_repository(settings: Settings = Depends(get_settings)) -> ProductRepository:
    return ProductRepository(get_mongo_database(), settings)


def get_store_repository(settings: Settings = Depends(get_settings)) -> PostgresStoreRepository:
    return PostgresStoreRepository(settings)


def page_url(path: str, **params: Any) -> str:
    clean = {key: value for key, value in params.items() if value not in (None, "")}
    if not clean:
        return path
    return f"{path}?{urlencode(clean)}"


def app_url(root_path: str, path: str, **params: Any) -> str:
    return f"{root_path}{page_url(path, **params)}"


def redirect_to(request: Request, path: str, **params: Any) -> RedirectResponse:
    return RedirectResponse(app_url(request.scope.get("root_path", ""), path, **params), status_code=303)


def localize_message(code: str | None) -> str | None:
    if code is None:
        return None
    return SUCCESS_MESSAGES.get(code, code)


def localize_error(error: str | None) -> str | None:
    if error is None:
        return None
    return ERROR_MESSAGES.get(error, error)


def localize_health(health: dict[str, Any]) -> dict[str, Any]:
    health["status_label"] = STATUS_LABELS.get(health.get("status"), health.get("status", ""))
    for item in health.get("databases", {}).values():
        item["status_label"] = STATUS_LABELS.get(item.get("status"), item.get("status", ""))
    return health


def render(request: Request, template: str, context: dict[str, Any], settings: Settings):
    root_path = request.scope.get("root_path", "")
    base_context = {
        "request": request,
        "root_path": root_path,
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "health": localize_health(get_health_status(settings)),
        "nav_links": [
            {"href": app_url(root_path, "/"), "label": "Обзор"},
            {"href": app_url(root_path, "/manage/products"), "label": "Товары"},
            {"href": app_url(root_path, "/manage/branches"), "label": "Филиалы"},
            {"href": app_url(root_path, "/manage/employees"), "label": "Сотрудники"},
            {"href": app_url(root_path, "/docs"), "label": "Swagger"},
        ],
    }
    base_context.update(context)
    base_context["message"] = localize_message(base_context.get("message"))
    base_context["error"] = localize_error(base_context.get("error"))
    return templates.TemplateResponse(template, base_context)


@router.get("/")
def home_page(request: Request, settings: Settings = Depends(get_settings)):
    return render(
        request,
        "index.html",
        {
            "summary_cards": [
                {"title": "MongoDB", "text": "Хранит каталог товаров и данные по остаткам."},
                {"title": "PostgreSQL", "text": "Хранит филиалы и сотрудников с реляционными связями."},
                {"title": "FastAPI", "text": "Отдаёт REST API, HTML-страницы и объединённый endpoint /health."},
                {"title": "Nginx", "text": "Работает как единая точка входа для масштабируемых контейнеров API."},
            ]
        },
        settings,
    )


@router.get("/manage/products")
def products_page(
    request: Request,
    message: str | None = None,
    error: str | None = None,
    settings: Settings = Depends(get_settings),
    products: ProductRepository = Depends(get_product_repository),
):
    return render(
        request,
        "manage_products.html",
        {
            "products": products.list_products(),
            "message": message,
            "error": error,
        },
        settings,
    )


@router.post("/manage/products")
def create_product_page(
    request: Request,
    name: str = Form(...),
    category: str = Form(...),
    price: float = Form(...),
    quantity: int = Form(...),
    manufacturer: str = Form(...),
    description: str = Form(...),
    products: ProductRepository = Depends(get_product_repository),
):
    try:
        products.create_product(
            {
                "name": name,
                "category": category,
                "price": price,
                "quantity": quantity,
                "manufacturer": manufacturer,
                "description": description,
            }
        )
    except HTTPException as exc:
        return redirect_to(request, "/manage/products", error=exc.detail)
    return redirect_to(request, "/manage/products", message="product-created")


@router.post("/manage/products/{product_id}/delete")
def delete_product_page(
    request: Request,
    product_id: str,
    products: ProductRepository = Depends(get_product_repository),
):
    try:
        products.delete_product(product_id)
    except HTTPException as exc:
        return redirect_to(request, "/manage/products", error=exc.detail)
    return redirect_to(request, "/manage/products", message="product-deleted")


@router.get("/manage/branches")
def branches_page(
    request: Request,
    message: str | None = None,
    error: str | None = None,
    settings: Settings = Depends(get_settings),
    store: PostgresStoreRepository = Depends(get_store_repository),
):
    return render(
        request,
        "manage_branches.html",
        {
            "branches": store.list_branches(),
            "message": message,
            "error": error,
        },
        settings,
    )


@router.post("/manage/branches")
def create_branch_page(
    request: Request,
    name: str = Form(...),
    city: str = Form(...),
    address: str = Form(...),
    store: PostgresStoreRepository = Depends(get_store_repository),
):
    try:
        store.create_branch({"name": name, "city": city, "address": address})
    except HTTPException as exc:
        return redirect_to(request, "/manage/branches", error=exc.detail)
    return redirect_to(request, "/manage/branches", message="branch-created")


@router.post("/manage/branches/{branch_id}/delete")
def delete_branch_page(
    request: Request,
    branch_id: int,
    store: PostgresStoreRepository = Depends(get_store_repository),
):
    try:
        store.delete_branch(branch_id)
    except HTTPException as exc:
        return redirect_to(request, "/manage/branches", error=exc.detail)
    return redirect_to(request, "/manage/branches", message="branch-deleted")


@router.get("/manage/employees")
def employees_page(
    request: Request,
    message: str | None = None,
    error: str | None = None,
    settings: Settings = Depends(get_settings),
    store: PostgresStoreRepository = Depends(get_store_repository),
):
    return render(
        request,
        "manage_employees.html",
        {
            "employees": store.list_employees(),
            "branches": store.list_branches(),
            "message": message,
            "error": error,
        },
        settings,
    )


@router.post("/manage/employees")
def create_employee_page(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    position: str = Form(...),
    email: str = Form(...),
    salary: float = Form(...),
    branch_id: int = Form(...),
    store: PostgresStoreRepository = Depends(get_store_repository),
):
    try:
        store.create_employee(
            {
                "first_name": first_name,
                "last_name": last_name,
                "position": position,
                "email": email,
                "salary": salary,
                "branch_id": branch_id,
            }
        )
    except HTTPException as exc:
        return redirect_to(request, "/manage/employees", error=exc.detail)
    return redirect_to(request, "/manage/employees", message="employee-created")


@router.post("/manage/employees/{employee_id}/delete")
def delete_employee_page(
    request: Request,
    employee_id: int,
    store: PostgresStoreRepository = Depends(get_store_repository),
):
    try:
        store.delete_employee(employee_id)
    except HTTPException as exc:
        return redirect_to(request, "/manage/employees", error=exc.detail)
    return redirect_to(request, "/manage/employees", message="employee-deleted")
