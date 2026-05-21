# Справочник по запросам

Этот файл показывает, где в интерфейсе реализован каждый из 10 запросов из задания.

## 10 запросов из задания

| № | Запрос | Где в интерфейсе | Кто использует | Прямой запрос к БД |
|---|---|---|---|---|
| 1 | Получение списка всех категорий | Главная страница каталога, блок `Категории` и выпадающий список фильтра | `guest`, `user`, `manager`, `admin` | `db.categories.find({})` |
| 2 | Получение списка всех продуктов в категории | Главная страница каталога, фильтр `Категория` или плашка категории | `guest`, `user`, `manager`, `admin` | `db.products.find({ categoryId: { $in: [ObjectId("..."), "665..."] } }).sort({ name: 1 })` |
| 3 | Поиск продукта по названию | Главная страница каталога, поле `Поиск` | `guest`, `user`, `manager`, `admin` | `db.products.find({ name: { $regex: "поиск", $options: "i" } }).sort({ name: 1 })` |
| 4 | Добавление продукта в корзину клиента | Карточка товара на главной странице, кнопка `В корзину` | `user` | `db.carts.findOne({ customerId: ObjectId("...") })` затем `db.carts.updateOne({ _id: ObjectId("...") }, { $set: { products: [...] } })`; если корзины нет, то `db.carts.insertOne({ customerId: ObjectId("..."), products: [] })` |
| 5 | Получение списка всех заказов клиента | Страница `/orders` | `user` | `db.orders.find({ customerId: { $in: [ObjectId("..."), "665..."] } }).sort({ orderDate: -1 })` |
| 6 | Обновление статуса заказа | Страница `/manager/analytics`, блок `Статусы заказов` | `manager` | `db.orders.updateOne({ _id: ObjectId("...") }, { $set: { status: "shipped", updated_at: new Date() } })` |
| 7 | Получение списка топ-продаж за последние месяцы с учетом цены и количества проданных товаров | Страница `/manager/analytics`, блок `Топ продаж` | `manager` | `db.orders.aggregate([{ $match: { orderDate: { $gte: ISODate("...") } } }, { $unwind: "$products" }, { $group: { _id: "$products.productId", name: { $first: "$products.name" }, quantity_sold: { $sum: "$products.quantity" }, revenue: { $sum: { $multiply: ["$products.price", "$products.quantity"] } } } }, { $sort: { revenue: -1, quantity_sold: -1 } }, { $limit: N }])` |
| 8 | Получение списка клиентов, которые сделали более чем N покупок в последнее время | Страница `/manager/analytics`, блок `Активные клиенты` | `manager` | `db.orders.aggregate([{ $match: { orderDate: { $gte: ISODate("...") } } }, { $group: { _id: "$customerId", orders_count: { $sum: 1 }, total_spent: { $sum: "$totalPrice" } } }, { $match: { orders_count: { $gt: N } } }, { $sort: { orders_count: -1, total_spent: -1 } }])` |
| 9 | Какие категории товаров пользовались спросом в заданный срок | Страница `/manager/analytics`, блок `Спрос по категориям` | `manager` | `db.orders.aggregate([{ $match: { orderDate: { $gte: ISODate("..."), $lte: ISODate("...") } } }, { $unwind: "$products" }, { $lookup: { from: "products", localField: "products.productId", foreignField: "_id", as: "product_doc" } }, { $unwind: "$product_doc" }, { $group: { _id: "$product_doc.categoryId", quantity_sold: { $sum: "$products.quantity" }, revenue: { $sum: { $multiply: ["$products.price", "$products.quantity"] } } } }, { $lookup: { from: "categories", localField: "_id", foreignField: "_id", as: "category_doc" } }, { $unwind: "$category_doc" }, { $sort: { quantity_sold: -1, revenue: -1 } }])` |
| 10 | Какие товары не были проданы в какую-то дату | Страница `/manager/analytics`, блок `Товары без продаж` | `manager` | `db.orders.distinct("products.productId", { orderDate: { $gte: ISODate("..."), $lte: ISODate("...") } })` затем `db.products.find({ _id: { $nin: soldIds } }).sort({ name: 1 })` |

## Запросы, которые выполняются напрямую в MongoDB

### Инициализация базы

Файл [`docker/mongo-init/01-init-shop.js`](docker/mongo-init/01-init-shop.js) выполняет прямые команды MongoDB:

- `db.dropDatabase()` - очистка базы перед инициализацией
- `db.createCollection(...)` - создание коллекций `categories`, `products`, `customers`, `employees`, `orders`, `carts`
- `$jsonSchema` + `validationLevel: "strict"` + `validationAction: "error"` - включение валидации документов
- `insertMany(...)` - заполнение коллекций демонстрационными данными
- `createIndex(...)` - создание индексов для поиска, фильтрации и ограничений уникальности
- `createRole(...)` - создание ролей MongoDB для `admin`, `manager`, `user`, `guest`
- `createUser(...)` - создание пользователей MongoDB для учебного стенда

### Основные запросы приложения к БД

Файл [`app/repositories.py`](app/repositories.py) и часть API вызывают MongoDB напрямую:

- `find(...)` - получение категорий, товаров, клиентов, корзин и заказов
- `findOne(...)` / `find_one(...)` - получение одного товара, клиента, корзины или заказа
- `insertOne(...)` / `insert_one(...)` - создание товара, клиента, корзины, заказа
- `updateOne(...)` / `update_one(...)` - обновление товара, корзины, статуса заказа и клиента
- `deleteOne(...)` / `delete_one(...)` - удаление товара или клиента
- `deleteMany(...)` / `delete_many(...)` - очистка связанных корзин и заказов клиента
- `aggregate(...)` - топ продаж, активные клиенты, спрос по категориям
- `distinct(...)` - поиск товаров без продаж на выбранную дату
- `createIndex(...)` - выполняется на этапе инициализации, но влияет на быстрые ответы этих запросов

## Как использовать

1. Открой главную страницу каталога и проверь пункты 1-4.
2. Открой `/orders` под ролью `user` и проверь пункт 5.
3. Открой `/manager/analytics` под ролью `manager` и проверь пункты 6-10.

## Кратко по ролям

- `guest` - просмотр каталога
- `user` - каталог, корзина и свои заказы
- `manager` - аналитика и управление статусами заказов
- `admin` - управление клиентами
