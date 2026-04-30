const express = require("express");
const cors = require("cors");
const authRoutes = require("./routes/authRoutes");
const jobRoutes = require("./routes/jobRoutes");
const applicationRoutes = require("./routes/applicationRoutes");
const app = express();

// Robust CORS configuration for production (Render/Vercel)
app.use(cors({
    origin: "*",
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
    optionsSuccessStatus: 200 // Some legacy browsers (IE11, various SmartTVs) choke on 204
}));
app.use(express.json());
app.use("/api/auth", authRoutes);
app.use("/api/jobs", jobRoutes);
app.use("/api/applications", applicationRoutes);

app.get("/", (req, res) => {
    res.send("API Running");
});

module.exports = app;