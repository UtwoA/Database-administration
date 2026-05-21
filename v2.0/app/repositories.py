from __future__ import annotations

from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status
from psycopg.errors import ForeignKeyViolation, UniqueViolation
from pymongo.database import Database

from app.config import Settings
from app.db import postgres_connection


def parse_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product id.")
    return ObjectId(value)


class ProductRepository:
    def __init__(self, db: Database, settings: Settings):
        self.db = db
        self.settings = settings

    @property
    def products(self):
        return self.db[self.settings.mongo_products_collection]

    def list_products(self) -> list[dict[str, Any]]:
        cursor = self.products.find({}).sort("name", 1)
        return [self._to_api(item) for item in cursor]

    def create_product(self, payload: dict[str, Any]) -> dict[str, Any]:
        document = {
            "name": payload["name"].strip(),
            "category": payload["category"].strip(),
            "price": float(payload["price"]),
            "quantity": int(payload["quantity"]),
            "manufacturer": payload["manufacturer"].strip(),
            "description": payload["description"].strip(),
        }
        result = self.products.insert_one(document)
        created = self.products.find_one({"_id": result.inserted_id})
        return self._to_api(created)

    def delete_product(self, product_id: str) -> dict[str, str]:
        result = self.products.delete_one({"_id": parse_object_id(product_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        return {"status": "deleted", "product_id": product_id}

    @staticmethod
    def _to_api(document: dict[str, Any] | None) -> dict[str, Any]:
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        return {
            "id": str(document["_id"]),
            "name": document["name"],
            "category": document["category"],
            "price": float(document["price"]),
            "quantity": int(document["quantity"]),
            "manufacturer": document["manufacturer"],
            "description": document["description"],
        }


class PostgresStoreRepository:
    def __init__(self, settings: Settings):
        self.settings = settings

    def list_branches(self) -> list[dict[str, Any]]:
        query = """
            SELECT id, name, city, address
            FROM branches
            ORDER BY city, name, id
        """
        with postgres_connection(self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                return [dict(row) for row in cursor.fetchall()]

    def create_branch(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = """
            INSERT INTO branches (name, city, address)
            VALUES (%s, %s, %s)
            RETURNING id, name, city, address
        """
        values = (
            payload["name"].strip(),
            payload["city"].strip(),
            payload["address"].strip(),
        )
        with postgres_connection(self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, values)
                branch = dict(cursor.fetchone())
            connection.commit()
        return branch

    def delete_branch(self, branch_id: int) -> dict[str, int | str]:
        query = "DELETE FROM branches WHERE id = %s RETURNING id"
        try:
            with postgres_connection(self.settings) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (branch_id,))
                    deleted = cursor.fetchone()
                connection.commit()
        except ForeignKeyViolation as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Branch has linked employees and cannot be removed.",
            ) from exc
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found.")
        return {"status": "deleted", "branch_id": branch_id}

    def list_employees(self) -> list[dict[str, Any]]:
        query = """
            SELECT
                e.id,
                e.first_name,
                e.last_name,
                e.position,
                e.email,
                e.salary,
                e.branch_id,
                b.name AS branch_name,
                b.city AS branch_city
            FROM employees e
            JOIN branches b ON b.id = e.branch_id
            ORDER BY e.id
        """
        with postgres_connection(self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                return [self._employee_from_row(dict(row)) for row in cursor.fetchall()]

    def create_employee(self, payload: dict[str, Any]) -> dict[str, Any]:
        branch = self.get_branch(payload["branch_id"])
        query = """
            INSERT INTO employees (first_name, last_name, position, email, salary, branch_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, first_name, last_name, position, email, salary, branch_id
        """
        values = (
            payload["first_name"].strip(),
            payload["last_name"].strip(),
            payload["position"].strip(),
            payload["email"].strip(),
            float(payload["salary"]),
            int(payload["branch_id"]),
        )
        try:
            with postgres_connection(self.settings) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, values)
                    employee = dict(cursor.fetchone())
                connection.commit()
        except UniqueViolation as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee with this email already exists.",
            ) from exc
        employee["branch_name"] = branch["name"]
        employee["branch_city"] = branch["city"]
        return self._employee_from_row(employee)

    def delete_employee(self, employee_id: int) -> dict[str, int | str]:
        query = "DELETE FROM employees WHERE id = %s RETURNING id"
        with postgres_connection(self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (employee_id,))
                deleted = cursor.fetchone()
            connection.commit()
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")
        return {"status": "deleted", "employee_id": employee_id}

    def get_branch(self, branch_id: int) -> dict[str, Any]:
        query = """
            SELECT id, name, city, address
            FROM branches
            WHERE id = %s
        """
        with postgres_connection(self.settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (branch_id,))
                branch = cursor.fetchone()
        if not branch:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch not found.")
        return dict(branch)

    @staticmethod
    def _employee_from_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": int(row["id"]),
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "position": row["position"],
            "email": row["email"],
            "salary": float(row["salary"]),
            "branch_id": int(row["branch_id"]),
            "branch_name": row.get("branch_name"),
            "branch_city": row.get("branch_city"),
        }
