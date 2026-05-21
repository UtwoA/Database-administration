# Справочник по запросам v2.0

Этот файл показывает, где в интерфейсе проверяется каждый обязательный сценарий практической работы № 2 и в какую БД идет операция.

## Основные сценарии

| № | Сценарий | Где проверять | База данных | HTTP/API |
|---|---|---|---|---|
| 1 | Получение списка товаров | Страница `/manage/products`, таблица каталога | MongoDB | `GET /products` |
| 2 | Добавление товара | Страница `/manage/products`, форма `Add product` | MongoDB | `POST /products` |
| 3 | Удаление товара | Страница `/manage/products`, кнопка `Delete` | MongoDB | `DELETE /products/{product_id}` |
| 4 | Получение списка филиалов | Страница `/manage/branches`, таблица филиалов | PostgreSQL | `GET /branches` |
| 5 | Добавление филиала | Страница `/manage/branches`, форма `Add branch` | PostgreSQL | `POST /branches` |
| 6 | Удаление филиала | Страница `/manage/branches`, кнопка `Delete` | PostgreSQL | `DELETE /branches/{branch_id}` |
| 7 | Получение списка сотрудников | Страница `/manage/employees`, таблица сотрудников | PostgreSQL | `GET /employees` |
| 8 | Добавление сотрудника | Страница `/manage/employees`, форма `Add employee` | PostgreSQL | `POST /employees` |
| 9 | Удаление сотрудника | Страница `/manage/employees`, кнопка `Delete` | PostgreSQL | `DELETE /employees/{employee_id}` |
| 10 | Проверка состояния обеих БД | Главная страница `/` и endpoint `/health` | MongoDB + PostgreSQL | `GET /health` |

## Что выполняется напрямую в MongoDB

Источник: `app/repositories.py`, класс `ProductRepository`, и `docker/mongo-init/01-init-store.js`.

- `insert_one(...)` - создание товара.
- `find(...)` - получение списка товаров.
- `delete_one(...)` - удаление товара.
- `createIndex(...)` - создание индексов при инициализации.
- `createUser(...)` - создание отдельного пользователя приложения.

## Что выполняется напрямую в PostgreSQL

Источник: `app/repositories.py`, класс `PostgresStoreRepository`, и `docker/postgres-init/01-init-store.sql`.

- `SELECT ... FROM branches` - получение списка филиалов.
- `INSERT INTO branches ... RETURNING ...` - создание филиала.
- `DELETE FROM branches ... RETURNING ...` - удаление филиала.
- `SELECT ... FROM employees JOIN branches ...` - получение списка сотрудников вместе с филиалом.
- `INSERT INTO employees ... RETURNING ...` - создание сотрудника.
- `DELETE FROM employees ... RETURNING ...` - удаление сотрудника.
- `REFERENCES branches(id) ON DELETE RESTRICT` - защита от удаления филиала, если к нему привязаны сотрудники.

## Как быстро проверить стенд

1. Открыть `/`.
2. Убедиться, что health-card показывает `ok` для MongoDB и PostgreSQL.
3. Перейти на `/manage/products`, добавить товар и удалить его.
4. Перейти на `/manage/branches`, добавить филиал.
5. Перейти на `/manage/employees`, добавить сотрудника в созданный филиал.
6. Удалить сотрудника.
7. Удалить тестовый филиал.
8. Открыть `/docs` и убедиться, что те же операции доступны как REST API.
