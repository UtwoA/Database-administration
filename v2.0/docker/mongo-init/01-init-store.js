const dbName = process.env.MONGO_DB_NAME || "hybrid_store";
const appUser = process.env.MONGO_APP_USER || "store_user";
const appPassword = process.env.MONGO_APP_PASSWORD || "store123";

db = db.getSiblingDB(dbName);

db.createCollection("products", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "category", "price", "quantity", "manufacturer", "description"],
      properties: {
        name: { bsonType: "string", minLength: 2 },
        category: { bsonType: "string", minLength: 2 },
        price: { bsonType: ["double", "int", "long", "decimal"], minimum: 0 },
        quantity: { bsonType: ["int", "long"], minimum: 0 },
        manufacturer: { bsonType: "string", minLength: 2 },
        description: { bsonType: "string", minLength: 3 },
      },
    },
  },
  validationLevel: "strict",
  validationAction: "error",
});

db.products.insertMany([
  {
    _id: ObjectId("665100000000000000000101"),
    name: "HP LaserJet Pro 4001dn",
    category: "Laser printers",
    price: 349.99,
    quantity: NumberInt(14),
    manufacturer: "HP",
    description: "Office monochrome laser printer with duplex printing.",
  },
  {
    _id: ObjectId("665100000000000000000102"),
    name: "Canon PIXMA G3470",
    category: "Inkjet printers",
    price: 229.5,
    quantity: NumberInt(11),
    manufacturer: "Canon",
    description: "Color inkjet printer with refillable tanks and Wi-Fi.",
  },
  {
    _id: ObjectId("665100000000000000000103"),
    name: "Epson EcoTank L3256",
    category: "Inkjet printers",
    price: 259.0,
    quantity: NumberInt(9),
    manufacturer: "Epson",
    description: "Compact multifunction inkjet device for home and study.",
  },
  {
    _id: ObjectId("665100000000000000000104"),
    name: "Brother HL-L2442DW",
    category: "Laser printers",
    price: 289.0,
    quantity: NumberInt(18),
    manufacturer: "Brother",
    description: "Wireless laser printer for small office workloads.",
  },
  {
    _id: ObjectId("665100000000000000000105"),
    name: "Anycubic Kobra 2 Neo",
    category: "3D printers",
    price: 319.0,
    quantity: NumberInt(6),
    manufacturer: "Anycubic",
    description: "Entry-level 3D printer with auto leveling and quiet motors.",
  },
]);

db.products.createIndex({ name: 1 });
db.products.createIndex({ category: 1 });
db.products.createIndex({ manufacturer: 1 });

db.createUser({
  user: appUser,
  pwd: appPassword,
  roles: [{ role: "readWrite", db: dbName }],
});

print("MongoDB hybrid store dataset initialized");
