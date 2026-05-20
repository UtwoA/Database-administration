const dbName = "shop";
db = db.getSiblingDB(dbName);

db.dropDatabase();

const ids = {
  categories: {
    laser: ObjectId("665000000000000000000001"),
    inkjet: ObjectId("665000000000000000000002"),
    led: ObjectId("665000000000000000000003"),
    mfp: ObjectId("665000000000000000000004"),
    supplies: ObjectId("665000000000000000000005"),
  },
  products: {
    hpLaserJet: ObjectId("665000000000000000000101"),
    canonPixma: ObjectId("665000000000000000000102"),
    epsonL805: ObjectId("665000000000000000000103"),
    pantumP2500w: ObjectId("665000000000000000000104"),
    brotherLed: ObjectId("665000000000000000000105"),
    xeroxMfp: ObjectId("665000000000000000000106"),
  },
  customers: {
    demo: ObjectId("665000000000000000000201"),
    alice: ObjectId("665000000000000000000202"),
    sofia: ObjectId("665000000000000000000203"),
  },
  employees: {
    manager: ObjectId("665000000000000000000301"),
    worker: ObjectId("665000000000000000000302"),
  },
};

db.createCollection("categories", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name"],
      properties: {
        name: { bsonType: "string", minLength: 3, description: "Category name is required" },
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
      required: ["customerId", "employeerId", "products", "totalPrice", "status", "deliveryAddress", "orderDate"],
      properties: {
        customerId: { bsonType: "objectId" },
        employeeId: { bsonType: "objectId" },
        employeerId: { bsonType: "objectId" },
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
  { _id: ids.categories.laser, name: "Laser printers" },
  { _id: ids.categories.inkjet, name: "Inkjet printers" },
  { _id: ids.categories.led, name: "LED printers" },
  { _id: ids.categories.mfp, name: "Multifunction printers" },
  { _id: ids.categories.supplies, name: "Printer supplies" },
]);

db.products.insertMany([
  { _id: ids.products.hpLaserJet, name: "HP LaserJet Pro M404dn", manufacturer: "HP", technology: "Laser", paperFormat: "A4", colors: NumberInt(1), price: 28990, quantity: NumberInt(12), categoryId: ids.categories.laser },
  { _id: ids.products.canonPixma, name: "Canon PIXMA G640", manufacturer: "Canon", technology: "Inkjet", paperFormat: "A4", colors: NumberInt(6), price: 34990, quantity: NumberInt(8), categoryId: ids.categories.inkjet },
  { _id: ids.products.epsonL805, name: "Epson L805", manufacturer: "Epson", technology: "Inkjet", paperFormat: "A4", colors: NumberInt(6), price: 41990, quantity: NumberInt(5), categoryId: ids.categories.inkjet },
  { _id: ids.products.pantumP2500w, name: "Pantum P2500W", manufacturer: "Pantum", technology: "Laser", paperFormat: "A4", colors: NumberInt(1), price: 12990, quantity: NumberInt(20), categoryId: ids.categories.laser },
  { _id: ids.products.brotherLed, name: "Brother HL-L8260CDW", manufacturer: "Brother", technology: "LED", paperFormat: "A4", colors: NumberInt(4), price: 53990, quantity: NumberInt(6), categoryId: ids.categories.led },
  { _id: ids.products.xeroxMfp, name: "Xerox B235 MFP", manufacturer: "Xerox", technology: "Laser", paperFormat: "A4", colors: NumberInt(1), price: 36990, quantity: NumberInt(7), categoryId: ids.categories.mfp },
]);

db.customers.insertMany([
  { _id: ids.customers.demo, firstName: "Demo", lastName: "Client", email: "demo.client@example.com", phone: "+79990000001" },
  { _id: ids.customers.alice, firstName: "Alice", lastName: "Ivanova", email: "alice@example.com", phone: "+79990000002" },
  { _id: ids.customers.sofia, firstName: "Sofia", lastName: "Petrova", email: "sofia@example.com", phone: "+79990000003" },
]);

db.employees.insertMany([
  { _id: ids.employees.manager, firstName: "Ivan", lastName: "Manager", position: "manager", email: "manager@example.com", salary: 120000 },
  { _id: ids.employees.worker, firstName: "Petr", lastName: "Worker", position: "worker", email: "worker@example.com", salary: 85000 },
]);

db.carts.insertMany([
  { customerId: ids.customers.demo, products: [] },
  { customerId: ids.customers.alice, products: [{ productId: ids.products.pantumP2500w, name: "Pantum P2500W", quantity: NumberInt(1), price: 12990 }] },
]);

db.orders.insertMany([
  {
    customerId: ids.customers.demo,
    employeeId: ids.employees.manager,
    employeerId: ids.employees.manager,
    products: [{ productId: ids.products.pantumP2500w, name: "Pantum P2500W", quantity: NumberInt(2), price: 12990 }],
    totalPrice: 25980,
    status: "delivered",
    deliveryAddress: "Moscow, Stromynka st., 20",
    orderDate: new Date("2026-04-25T10:00:00Z"),
  },
  {
    customerId: ids.customers.demo,
    employeeId: ids.employees.manager,
    employeerId: ids.employees.manager,
    products: [{ productId: ids.products.canonPixma, name: "Canon PIXMA G640", quantity: NumberInt(1), price: 34990 }],
    totalPrice: 34990,
    status: "shipped",
    deliveryAddress: "Moscow, Vernadskogo ave., 78",
    orderDate: new Date("2026-05-07T12:30:00Z"),
  },
  {
    customerId: ids.customers.alice,
    employeeId: ids.employees.worker,
    employeerId: ids.employees.worker,
    products: [
      { productId: ids.products.hpLaserJet, name: "HP LaserJet Pro M404dn", quantity: NumberInt(1), price: 28990 },
      { productId: ids.products.xeroxMfp, name: "Xerox B235 MFP", quantity: NumberInt(1), price: 36990 },
    ],
    totalPrice: 65980,
    status: "processing",
    deliveryAddress: "Moscow, Lenina st., 12",
    orderDate: new Date("2026-05-10T09:15:00Z"),
  },
]);

db.products.createIndex({ name: "text", manufacturer: "text" });
db.products.createIndex({ categoryId: 1 });
db.products.createIndex({ technology: 1, paperFormat: 1 });
db.orders.createIndex({ customerId: 1, orderDate: -1 });
db.orders.createIndex({ status: 1 });
db.carts.createIndex({ customerId: 1 }, { unique: true });
db.customers.createIndex({ email: 1 }, { unique: true });

db.createUser({ user: "shop_admin", pwd: "shop_admin_password", roles: [{ role: "readWrite", db: dbName }, { role: "dbAdmin", db: dbName }] });
db.createUser({ user: "shop_manager", pwd: "shop_manager_password", roles: [{ role: "readWrite", db: dbName }] });
db.createUser({ user: "shop_user", pwd: "shop_user_password", roles: [{ role: "readWrite", db: dbName }] });
db.createUser({ user: "shop_guest", pwd: "shop_guest_password", roles: [{ role: "read", db: dbName }] });

print("Printer shop database initialized");
