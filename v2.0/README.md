# Hybrid Store Stand v2.0

Учебный стенд для практической работы № 2 по дисциплине «Администрирование баз данных». В этой версии приложение разделяет хранение данных между двумя СУБД:

- MongoDB хранит каталог товаров.
- PostgreSQL хранит филиалы и сотрудников.
- FastAPI объединяет оба источника данных в одном API и HTML-интерфейсе.
- Nginx выступает точкой входа и позволяет масштабировать `api` через Docker Compose.

## Структура проекта

- `app/` - FastAPI-приложение, маршруты страниц и репозитории доступа к БД.
- `docker/mongo-init/` - инициализация MongoDB.
- `docker/postgres-init/` - инициализация PostgreSQL.
- `docker/nginx/` - конфигурация reverse proxy.
- `templates/` - HTML-страницы для ручной проверки.
- `static/` - стили интерфейса.
- `requests.md` - шпаргалка по запросам и сценариям проверки.

## Что реализовано

- `GET /health` - объединенный health-check по MongoDB и PostgreSQL.
- `GET /products`, `POST /products`, `DELETE /products/{product_id}` - работа с товарами в MongoDB.
- `GET /branches`, `POST /branches`, `DELETE /branches/{branch_id}` - работа с филиалами в PostgreSQL.
- `GET /employees`, `POST /employees`, `DELETE /employees/{employee_id}` - работа с сотрудниками в PostgreSQL.
- HTML-страницы:
  - `/` - обзор стенда.
  - `/manage/products` - управление товарами.
  - `/manage/branches` - управление филиалами.
  - `/manage/employees` - управление сотрудниками.

## Запуск стенда

В каталоге `v2.0` уже лежит готовый `.env`. При необходимости можно восстановить его из `.env.example`.

Запуск:

```bash
docker compose up -d --build
docker compose ps
```

После старта:

- UI и Swagger через Nginx: `http://127.0.0.1:8080/`
- Swagger: `http://127.0.0.1:8080/docs`
- Health: `http://127.0.0.1:8080/health`
- MongoDB: `127.0.0.1:27017`
- PostgreSQL: `127.0.0.1:5432`

Ожидаемый ответ `/health`:

```json
{
  "status": "ok",
  "application": {
    "name": "Hybrid Store Stand",
    "version": "2.0.0"
  },
  "databases": {
    "mongodb": {
      "status": "connected"
    },
    "postgresql": {
      "status": "connected"
    }
  }
}
```

## Масштабирование сервера приложений

Входная точка опубликована только у `nginx`, поэтому сервис `api` можно масштабировать без конфликтов по портам:

```bash
docker compose up -d --scale api=2
docker compose ps
```

Проверка после масштабирования:

- интерфейс по `http://127.0.0.1:8080/` продолжает открываться;
- `/health` по-прежнему отвечает успешно;
- Nginx продолжает проксировать запросы к сервису `api`.

## Обновление версии приложения

Чтобы воспроизвести обновление версии образа приложения:

1. Измените в `.env` значения `API_IMAGE_TAG` и `API_BUILD_VERSION`, например на `2.0.1`.
2. При необходимости обновите `APP_VERSION`.
3. Перезапустите сборку:

```bash
docker compose up -d --build
```

После этого проверьте:

- что контейнер `api` пересоздан;
- что `/health` отвечает успешно;
- что в ответе health-check и на главной странице отображается новая версия приложения.

## Очистка ресурсов

Остановить контейнеры:

```bash
docker compose down
```

Остановить контейнеры и удалить volumes MongoDB/PostgreSQL:

```bash
docker compose down -v
```

После повторного запуска контейнеры заново выполнят init-скрипты и загрузят тестовые данные.

## Данные и администрирование БД

### MongoDB

База `hybrid_store` хранит коллекцию `products` со следующими полями:

- `_id`
- `name`
- `category`
- `price`
- `quantity`
- `manufacturer`
- `description`

Init-скрипт:

- создает коллекцию с `$jsonSchema`-валидацией;
- заполняет демонстрационный каталог;
- создает индексы по `name`, `category`, `manufacturer`;
- создает отдельного пользователя приложения `store_user`.

### PostgreSQL

В PostgreSQL создаются таблицы:

- `branches`
- `employees`

Логическая модель:

- каждый филиал хранит `id`, `name`, `city`, `address`;
- каждый сотрудник хранит `id`, `first_name`, `last_name`, `position`, `email`, `salary`, `branch_id`;
- `employees.branch_id` ссылается на `branches.id`.

Init-скрипт:

- создает таблицы и индексы;
- загружает тестовые филиалы;
- загружает тестовых сотрудников;
- настраивает последовательности `SERIAL` после seed-заполнения.

### Что показывает v2.0 с точки зрения БД

- раздельное хранение данных в документной и реляционной СУБД;
- инициализацию обеих БД через Docker Compose;
- хранение параметров подключения в environment variables;
- работу приложения сразу с двумя БД в одном API;
- ограничение целостности в PostgreSQL через внешний ключ `employees.branch_id`;
- валидацию документов в MongoDB через `$jsonSchema`.
