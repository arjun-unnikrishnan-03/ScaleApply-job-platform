require("dotenv").config();
const app = require("./src/app");
const connectDB = require("./src/config/db");
const http = require("http");
const { Server } = require("socket.io");

connectDB();
const PORT = process.env.PORT || 5000;

const server = http.createServer(app);

const io = new Server(server, {
    cors: {
        origin: "*"
    }
});

// Make io globally accessible via req.app.get("io")
app.set("io", io);

io.on("connection", (socket) => {
    console.log("Socket Client connected:", socket.id);

    socket.on("disconnect", () => {
        console.log("Socket Client disconnected:", socket.id);
    });
});

server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});