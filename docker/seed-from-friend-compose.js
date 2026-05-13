db = db.getSiblingDB("shop");

db.dropDatabase();

const categories = {
  laser: ObjectId("665000000000000000000001"),
  inkjet: ObjectId("665000000000000000000002"),
  threeD: ObjectId("665000000000000000000003"),
  office: ObjectId("665000000000000000000004"),
  photo: ObjectId("665000000000000000000005"),
};

const products = {
  hpLaser: ObjectId("665000000000000000000101"),
  canonPixma: ObjectId("665000000000000000000102"),
  epsonEcoTank: ObjectId("665000000000000000000103"),
  anycubic: ObjectId("665000000000000000000104"),
  brotherLaser: ObjectId("665000000000000000000105"),
  hpDesignJet: ObjectId("665000000000000000000106"),
  canonSelphy: ObjectId("665000000000000000000107"),
};

const customers = {
  demo: ObjectId("665000000000000000000201"),
  alice: ObjectId("665000000000000000000202"),
};

const employees = {
  manager: ObjectId("665000000000000000000301"),
};

db.createCollection("categories", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name"],
      properties: { name: { bsonType: "string", minLength: 3 } },
    },
  },
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
});

db.categories.insertMany([
  { _id: categories.laser, name: "Laser Printers" },
  { _id: categories.inkjet, name: "Inkjet Printers" },
  { _id: categories.threeD, name: "3D Printers" },
  { _id: categories.office, name: "Office Printers" },
  { _id: categories.photo, name: "Photo Printers" },
]);

db.products.insertMany([
  { _id: products.hpLaser, name: "HP LaserJet Pro M404", quantity: NumberInt(15), price: 299.99, manufacturer: "HP", technology: "Laser", paperFormat: "A4", colors: NumberInt(1), categoryId: categories.laser },
  { _id: products.canonPixma, name: "Canon PIXMA G3411", quantity: NumberInt(20), price: 199.99, manufacturer: "Canon", technology: "Inkjet", paperFormat: "A4", colors: NumberInt(4), categoryId: categories.inkjet },
  { _id: products.epsonEcoTank, name: "Epson EcoTank L3250", quantity: NumberInt(10), price: 249.99, manufacturer: "Epson", technology: "Inkjet", paperFormat: "A4", colors: NumberInt(4), categoryId: categories.inkjet },
  { _id: products.anycubic, name: "Anycubic Kobra 2", quantity: NumberInt(5), price: 450, manufacturer: "Anycubic", technology: "3D", paperFormat: "A3", colors: NumberInt(1), categoryId: categories.threeD },
  { _id: products.brotherLaser, name: "Brother HL-L2370DN", quantity: NumberInt(12), price: 320, manufacturer: "Brother", technology: "Laser", paperFormat: "A4", colors: NumberInt(1), categoryId: categories.laser },
  { _id: products.hpDesignJet, name: "HP DesignJet T650", quantity: NumberInt(4), price: 1200, manufacturer: "HP", technology: "Inkjet", paperFormat: "A3", colors: NumberInt(4), categoryId: categories.office },
  { _id: products.canonSelphy, name: "Canon SELPHY CP1500", quantity: NumberInt(8), price: 180, manufacturer: "Canon", technology: "Inkjet", paperFormat: "A5", colors: NumberInt(4), categoryId: categories.photo },
]);

db.customers.insertMany([
  { _id: customers.demo, firstName: "Demo", lastName: "Client", email: "demo.client@example.com", phone: "+79990000001" },
  { _id: customers.alice, firstName: "Alice", lastName: "Ivanova", email: "alice@example.com", phone: "+79990000002" },
]);

db.employees.insertOne({
  _id: employees.manager,
  firstName: "Ivan",
  lastName: "Manager",
  position: "manager",
  email: "manager@example.com",
  salary: 120000,
});

db.carts.insertMany([
  { customerId: customers.demo, products: [] },
  { customerId: customers.alice, products: [{ productId: products.brotherLaser, name: "Brother HL-L2370DN", quantity: NumberInt(1), price: 320 }] },
]);

db.orders.insertMany([
  {
    customerId: customers.demo,
    employeeId: employees.manager,
    employeerId: employees.manager,
    products: [{ productId: products.hpLaser, name: "HP LaserJet Pro M404", quantity: NumberInt(2), price: 299.99 }],
    totalPrice: 599.98,
    status: "delivered",
    deliveryAddress: "Moscow, Stromynka st., 20",
    orderDate: new Date("2026-04-25T10:00:00Z"),
  },
  {
    customerId: customers.demo,
    employeeId: employees.manager,
    employeerId: employees.manager,
    products: [{ productId: products.canonPixma, name: "Canon PIXMA G3411", quantity: NumberInt(1), price: 199.99 }],
    totalPrice: 199.99,
    status: "shipped",
    deliveryAddress: "Moscow, Vernadskogo ave., 78",
    orderDate: new Date("2026-05-07T12:30:00Z"),
  },
]);

db.products.createIndex({ name: "text", manufacturer: "text" });
db.products.createIndex({ categoryId: 1 });
db.products.createIndex({ technology: 1, paperFormat: 1 });
db.orders.createIndex({ customerId: 1, orderDate: -1 });
db.carts.createIndex({ customerId: 1 }, { unique: true });
db.customers.createIndex({ email: 1 }, { unique: true });

print("Seeded shop database for friend docker-compose");
