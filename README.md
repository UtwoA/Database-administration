# Printer Shop MongoDB Stand

Educational MongoDB stand for a printer online shop practical work.

The project includes:

- MongoDB in Docker
- mongo-express for database inspection
- seed script with collections, validation, indexes, and demo data
- FastAPI API
- web UI: catalog, cart, orders, product management, and analytics

## 1. Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env` if it does not exist:

```powershell
Copy-Item .env.example .env
```

Default real database settings:

```env
USE_MOCK_DATA=false
MONGO_URI=mongodb://admin:admin123@localhost:27017/shop?authSource=admin
```

## 2. Start MongoDB

Start Docker containers:

```powershell
docker compose up -d
```

Check status:

```powershell
docker compose ps
```

Expected containers:

- `printer_store_mongo`
- `printer_store_express`

## 3. Seed Database

Run this when the database is empty or was recreated:

```powershell
Get-Content docker\seed-from-friend-compose.js | docker exec -i printer_store_mongo mongosh --username admin --password admin123 --authenticationDatabase admin
```

The seed script creates the `shop` database, collections, validation rules, indexes, and demo data.

Main demo customer id:

```text
665000000000000000000201
```

## 4. Start App

```powershell
python -m uvicorn app.main:app --reload
```

Open the web UI:

```text
http://127.0.0.1:8000/?role=user&client_id=665000000000000000000201
```

Open Swagger/OpenAPI:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok","database":"connected"}
```

## 5. mongo-express

URL:

```text
http://127.0.0.1:8081
```

Login:

```text
admin
```

Password:

```text
pass
```

## 6. Manual Test Scenario

1. Open the catalog.
2. Set role to `user`.
3. Set client id to `665000000000000000000201`.
4. Test filter `Technology = Laser`.
5. Add a product to the cart.
6. Open `Cart`.
7. Check the total price.
8. Click `Create order`.
9. Open `Orders`.
10. Change role to `manager`.
11. Open `Analytics`.
12. Check top sales, active clients, category demand, and order statuses.

## 7. Recreate Database

Use this when you need a clean database:

```powershell
docker compose down -v
docker compose up -d
Get-Content docker\seed-from-friend-compose.js | docker exec -i printer_store_mongo mongosh --username admin --password admin123 --authenticationDatabase admin
```

## 8. Mock Mode

If Docker or MongoDB is unavailable, enable mock mode in `.env`:

```env
USE_MOCK_DATA=true
```

Restart the app:

```powershell
python -m uvicorn app.main:app --reload
```

To return to MongoDB:

```env
USE_MOCK_DATA=false
```
