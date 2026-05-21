from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from psycopg import Error as PsycopgError
from pymongo.errors import PyMongoError

from app.config import Settings, get_settings
from app.db import get_health_status, get_mongo_database
from app.pages import router as pages_router
from app.repositories import PostgresStoreRepository, ProductRepository


settings = get_settings()
templates = Jinja2Templates(directory="templates")

app = FastAPI(
    title=settings.app_name,
    description="Hybrid store stand with MongoDB products and PostgreSQL staff/branches.",
    version=settings.app_version,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(pages_router, include_in_schema=False)


def get_product_repository(settings: Settings = Depends(get_settings)) -> ProductRepository:
    return ProductRepository(get_mongo_database(), settings)


def get_store_repository(settings: Settings = Depends(get_settings)) -> PostgresStoreRepository:
    return PostgresStoreRepository(settings)


def template_base_context(request: Request) -> dict[str, object]:
    health = get_health_status(settings)
    root_path = request.scope.get("root_path", "")
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "health": health,
        "nav_links": [
            {"href": f"{root_path}/", "label": "Overview"},
            {"href": f"{root_path}/manage/products", "label": "Products"},
            {"href": f"{root_path}/manage/branches", "label": "Branches"},
            {"href": f"{root_path}/manage/employees", "label": "Employees"},
            {"href": f"{root_path}/docs", "label": "Swagger"},
        ],
    }


@app.exception_handler(PyMongoError)
def mongodb_exception_handler(request: Request, exc: PyMongoError):
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            "db_error.html",
            {
                "request": request,
                **template_base_context(request),
                "db_name": "MongoDB",
                "error": str(exc),
            },
            status_code=503,
        )
    return JSONResponse(
        status_code=503,
        content={"detail": "MongoDB is unavailable.", "error": str(exc)},
    )


@app.exception_handler(PsycopgError)
def postgresql_exception_handler(request: Request, exc: PsycopgError):
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            "db_error.html",
            {
                "request": request,
                **template_base_context(request),
                "db_name": "PostgreSQL",
                "error": str(exc),
            },
            status_code=503,
        )
    return JSONResponse(
        status_code=503,
        content={"detail": "PostgreSQL is unavailable.", "error": str(exc)},
    )


class ProductCreate(BaseModel):
    name: str = Field(min_length=2)
    category: str = Field(min_length=2)
    price: float = Field(ge=0)
    quantity: int = Field(ge=0)
    manufacturer: str = Field(min_length=2)
    description: str = Field(min_length=3)


class BranchCreate(BaseModel):
    name: str = Field(min_length=2)
    city: str = Field(min_length=2)
    address: str = Field(min_length=5)


class EmployeeCreate(BaseModel):
    first_name: str = Field(min_length=2)
    last_name: str = Field(min_length=2)
    position: str = Field(min_length=2)
    email: str = Field(min_length=5)
    salary: float = Field(ge=0)
    branch_id: int = Field(gt=0)


@app.get("/health")
def health(response: Response, settings: Settings = Depends(get_settings)):
    payload = get_health_status(settings)
    if payload["status"] != "ok":
        response.status_code = 503
    return payload


@app.get("/products")
def list_products(products: ProductRepository = Depends(get_product_repository)):
    return products.list_products()


@app.post("/products", status_code=201)
def create_product(payload: ProductCreate, products: ProductRepository = Depends(get_product_repository)):
    return products.create_product(payload.model_dump())


@app.delete("/products/{product_id}")
def delete_product(product_id: str, products: ProductRepository = Depends(get_product_repository)):
    return products.delete_product(product_id)


@app.get("/branches")
def list_branches(store: PostgresStoreRepository = Depends(get_store_repository)):
    return store.list_branches()


@app.post("/branches", status_code=201)
def create_branch(payload: BranchCreate, store: PostgresStoreRepository = Depends(get_store_repository)):
    return store.create_branch(payload.model_dump())


@app.delete("/branches/{branch_id}")
def delete_branch(branch_id: int, store: PostgresStoreRepository = Depends(get_store_repository)):
    return store.delete_branch(branch_id)


@app.get("/employees")
def list_employees(store: PostgresStoreRepository = Depends(get_store_repository)):
    return store.list_employees()


@app.post("/employees", status_code=201)
def create_employee(payload: EmployeeCreate, store: PostgresStoreRepository = Depends(get_store_repository)):
    return store.create_employee(payload.model_dump())


@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, store: PostgresStoreRepository = Depends(get_store_repository)):
    return store.delete_employee(employee_id)
