const mongoose = require('mongoose');
require('dotenv').config();

console.log("Connecting to MongoDB:", process.env.MONGO_URI ? "URI Loaded" : "No URI");

mongoose.connect(process.env.MONGO_URI)
  .then(() => {
    console.log("✅ Success! MongoDB is connected and reachable.");
    process.exit(0);
  })
  .catch(err => {
    console.error("❌ Failed to connect to MongoDB:", err.message);
    process.exit(1);
  });
