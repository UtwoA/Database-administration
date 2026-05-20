const dbName = "shop";
db = db.getSiblingDB(dbName);

db.dropDatabase();

const ids = {
  categories: {
    laser: ObjectId("665000000000000000000001"),
    inkjet: ObjectId("665000000000000000000002"),
    threeD: ObjectId("665000000000000000000003"),
    office: ObjectId("665000000000000000000004"),
    photo: ObjectId("665000000000000000000005"),
  },
  products: {
    hpLaser: ObjectId("665000000000000000000101"),
    canonPixma: ObjectId("665000000000000000000102"),
    epsonEcoTank: ObjectId("665000000000000000000103"),
    anycubic: ObjectId("665000000000000000000104"),
    brotherLaser: ObjectId("665000000000000000000105"),
    hpDesignJet: ObjectId("665000000000000000000106"),
    canonSelphy: ObjectId("665000000000000000000107"),
  },
  customers: {
    demo: ObjectId("665000000000000000000201"),
    alice: ObjectId("665000000000000000000202"),
    sofia: ObjectId("665000000000000000000203"),
  },
  employees: {
    manager: ObjectId("665000000000000000000301"),
    analyst: ObjectId("665000000000000000000302"),
  },
};

db.createCollection("categories", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name"],
      properties: {
        name: { bsonType: "string", minLength: 3 },
      },
    },
  },
  validationLevel: "strict",
  validationAction: "error",
});

db.createCollection("products", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "manufacturer", "technology", "paperFormat", "colors", "price", "categoryId"],
      properties: {
        name: { bsonType: "string", minLength: 3 },
        manufacturer: { bsonType: "string" },
        technology: { enum: ["Laser", "Inkjet", "LED", "3D"] },
        paperFormat: { enum: ["A4", "A3", "A5"] },
        colors: { bsonType: "int", minimum: 1 },
        price: { bsonType: ["int", "double"], minimum: 0 },
        quantity: { bsonType: "int", minimum: 0 },
        categoryId: { bsonType: "objectId" },
        characteristics: { bsonType: "object" },
      },
    },
  },
  validationLevel: "strict",
  validationAction: "error",
});

db.createCollection("customers", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["firstName", "lastName", "email", "phone"],
      properties: {
        firstName: { bsonType: "string" },
        lastName: { bsonType: "string" },
        email: { bsonType: "string", pattern: "^.+@.+$" },
        phone: { bsonType: "string" },
      },
    },
  },
  validationLevel: "strict",
  validationAction: "error",
});

db.createCollection("employees", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["firstName", "lastName", "position", "email", "salary"],
      properties: {
        firstName: { bsonType: "string" },
        lastName: { bsonType: "string" },
        position: { bsonType: "string" },
        email: { bsonType: "string" },
        salary: { bsonType: ["int", "double"], minimum: 0 },
      },
    },
  },
  validationLevel: "strict",
  validationAction: "error",
});

db.createCollection("orders", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["customerId", "employeeId", "products", "totalPrice", "status", "deliveryAddress", "orderDate"],
      properties: {
        customerId: { bsonType: "objectId" },
        employeeId: { bsonType: "objectId" },
        products: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["productId", "name", "quantity", "price"],
            properties: {
              productId: { bsonType: "objectId" },
              name: { bsonType: "string" },
              quantity: { bsonType: "int", minimum: 1 },
              price: { bsonType: ["int", "double"], minimum: 0 },
            },
          },
        },
        totalPrice: { bsonType: ["int", "double"], minimum: 0 },
        status: { enum: ["processing", "shipped", "delivered", "cancelled"] },
        deliveryAddress: { bsonType: "string" },
        orderDate: { bsonType: "date" },
      },
    },
  },
  validationLevel: "strict",
  validationAction: "error",
});

db.createCollection("carts", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["customerId", "products"],
      properties: {
        customerId: { bsonType: "objectId" },
        products: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["productId", "name", "quantity", "price"],
            properties: {
              productId: { bsonType: "objectId" },
              name: { bsonType: "string" },
              quantity: { bsonType: "int", minimum: 1 },
              price: { bsonType: ["int", "double"], minimum: 0 },
            },
          },
        },
      },
    },
  },
  validationLevel: "strict",
  validationAction: "error",
});

db.categories.insertMany([
  { _id: ids.categories.laser, name: "Laser Printers" },
  { _id: ids.categories.inkjet, name: "Inkjet Printers" },
  { _id: ids.categories.threeD, name: "3D Printers" },
  { _id: ids.categories.office, name: "Office Printers" },
  { _id: ids.categories.photo, name: "Photo Printers" },
]);

db.products.insertMany([
  { _id: ids.products.hpLaser, name: "HP LaserJet Pro M404", quantity: NumberInt(15), price: 299.99, manufacturer: "HP", technology: "Laser", paperFormat: "A4", colors: NumberInt(1), categoryId: ids.categories.laser, characteristics: { print_speed: "38 ppm", resolution: "1200x1200", tray_capacity: "250" } },
  { _id: ids.products.canonPixma, name: "Canon PIXMA G3411", quantity: NumberInt(20), price: 199.99, manufacturer: "Canon", technology: "Inkjet", paperFormat: "A4", colors: NumberInt(4), categoryId: ids.categories.inkjet, characteristics: { print_speed: "9 ppm", resolution: "4800x1200", tray_capacity: "100" } },
  { _id: ids.products.epsonEcoTank, name: "Epson EcoTank L3250", quantity: NumberInt(10), price: 249.99, manufacturer: "Epson", technology: "Inkjet", paperFormat: "A4", colors: NumberInt(4), categoryId: ids.categories.inkjet, characteristics: { print_speed: "10 ppm", resolution: "5760x1440", tray_capacity: "100" } },
  { _id: ids.products.anycubic, name: "Anycubic Kobra 2", quantity: NumberInt(5), price: 450, manufacturer: "Anycubic", technology: "3D", paperFormat: "A3", colors: NumberInt(1), categoryId: ids.categories.threeD, characteristics: { print_speed: "250 mm/s", resolution: "0.1 mm", tray_capacity: "1 spool" } },
  { _id: ids.products.brotherLaser, name: "Brother HL-L2370DN", quantity: NumberInt(12), price: 320, manufacturer: "Brother", technology: "Laser", paperFormat: "A4", colors: NumberInt(1), categoryId: ids.categories.laser, characteristics: { print_speed: "34 ppm", resolution: "1200x1200", tray_capacity: "250" } },
  { _id: ids.products.hpDesignJet, name: "HP DesignJet T650", quantity: NumberInt(4), price: 1200, manufacturer: "HP", technology: "Inkjet", paperFormat: "A3", colors: NumberInt(4), categoryId: ids.categories.office, characteristics: { print_speed: "25 sec/page", resolution: "2400x1200", tray_capacity: "150" } },
  { _id: ids.products.canonSelphy, name: "Canon SELPHY CP1500", quantity: NumberInt(8), price: 180, manufacturer: "Canon", technology: "Inkjet", paperFormat: "A5", colors: NumberInt(4), categoryId: ids.categories.photo, characteristics: { print_speed: "41 sec/photo", resolution: "300x300", tray_capacity: "18" } },
]);

db.customers.insertMany([
  { _id: ids.customers.demo, firstName: "Demo", lastName: "Client", email: "demo.client@example.com", phone: "+79990000001" },
  { _id: ids.customers.alice, firstName: "Alice", lastName: "Ivanova", email: "alice@example.com", phone: "+79990000002" },
  { _id: ids.customers.sofia, firstName: "Sofia", lastName: "Petrova", email: "sofia@example.com", phone: "+79990000003" },
]);

db.employees.insertMany([
  { _id: ids.employees.manager, firstName: "Ivan", lastName: "Manager", position: "manager", email: "manager@example.com", salary: 120000 },
  { _id: ids.employees.analyst, firstName: "Elena", lastName: "Analyst", position: "analyst", email: "analyst@example.com", salary: 98000 },
]);

db.carts.insertMany([
  { customerId: ids.customers.demo, products: [] },
  { customerId: ids.customers.alice, products: [{ productId: ids.products.brotherLaser, name: "Brother HL-L2370DN", quantity: NumberInt(1), price: 320 }] },
  { customerId: ids.customers.sofia, products: [{ productId: ids.products.anycubic, name: "Anycubic Kobra 2", quantity: NumberInt(1), price: 450 }] },
]);

db.orders.insertMany([
  { customerId: ids.customers.demo, employeeId: ids.employees.manager, products: [{ productId: ids.products.hpLaser, name: "HP LaserJet Pro M404", quantity: NumberInt(2), price: 299.99 }], totalPrice: 599.98, status: "delivered", deliveryAddress: "Moscow, Stromynka st., 20", orderDate: new Date("2026-04-25T10:00:00Z") },
  { customerId: ids.customers.demo, employeeId: ids.employees.manager, products: [{ productId: ids.products.canonPixma, name: "Canon PIXMA G3411", quantity: NumberInt(1), price: 199.99 }], totalPrice: 199.99, status: "shipped", deliveryAddress: "Moscow, Vernadskogo ave., 78", orderDate: new Date("2026-05-07T12:30:00Z") },
  { customerId: ids.customers.alice, employeeId: ids.employees.analyst, products: [{ productId: ids.products.hpDesignJet, name: "HP DesignJet T650", quantity: NumberInt(1), price: 1200 }], totalPrice: 1200, status: "processing", deliveryAddress: "Moscow, Arbat st., 15", orderDate: new Date("2026-05-10T09:15:00Z") },
]);

db.products.createIndex({ name: "text", manufacturer: "text" });
db.products.createIndex({ categoryId: 1 });
db.products.createIndex({ technology: 1, paperFormat: 1 });
db.orders.createIndex({ customerId: 1, orderDate: -1 });
db.orders.createIndex({ status: 1 });
db.carts.createIndex({ customerId: 1 }, { unique: true });
db.customers.createIndex({ email: 1 }, { unique: true });

db.createRole({ role: "shopAdminRole", privileges: [{ resource: { db: dbName, collection: "" }, actions: ["anyAction"] }], roles: [] });
db.createRole({ role: "shopManagerRole", privileges: [{ resource: { db: dbName, collection: "products" }, actions: ["find", "insert", "update", "remove"] }, { resource: { db: dbName, collection: "categories" }, actions: ["find", "insert", "update"] }, { resource: { db: dbName, collection: "orders" }, actions: ["find", "update"] }], roles: [] });
db.createRole({ role: "shopUserRole", privileges: [{ resource: { db: dbName, collection: "products" }, actions: ["find"] }, { resource: { db: dbName, collection: "categories" }, actions: ["find"] }, { resource: { db: dbName, collection: "carts" }, actions: ["find", "insert", "update"] }, { resource: { db: dbName, collection: "orders" }, actions: ["find", "insert"] }], roles: [] });
db.createRole({ role: "shopGuestRole", privileges: [{ resource: { db: dbName, collection: "products" }, actions: ["find"] }, { resource: { db: dbName, collection: "categories" }, actions: ["find"] }], roles: [] });

db.createUser({ user: "shop_admin", pwd: "admin123", roles: [{ role: "shopAdminRole", db: dbName }] });
db.createUser({ user: "shop_manager", pwd: "manager123", roles: [{ role: "shopManagerRole", db: dbName }] });
db.createUser({ user: "shop_user", pwd: "user123", roles: [{ role: "shopUserRole", db: dbName }] });
db.createUser({ user: "shop_guest", pwd: "guest123", roles: [{ role: "shopGuestRole", db: dbName }] });

print("Printer shop database initialized");
