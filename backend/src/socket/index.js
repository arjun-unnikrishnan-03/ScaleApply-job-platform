const { Server } = require("socket.io");
const jwt = require("jsonwebtoken");
const env = require("../config/env");
const logger = require("../utils/logger");

let io = null;

const recruiterRoom = (id) => `recruiter:${id}`;
const userRoom = (id) => `user:${id}`;

const initSocket = (httpServer) => {
    io = new Server(httpServer, {
        cors: { origin: env.corsOrigins.length ? env.corsOrigins : false, credentials: true },
        pingTimeout: 30000
    });

    io.use((socket, next) => {
        const token = socket.handshake.auth?.token;
        if (!token) return next(new Error("Unauthorized"));
        try {
            const decoded = jwt.verify(token, env.jwtSecret);
            socket.data.userId = decoded.id;
            socket.data.role = decoded.role;
            next();
        } catch {
            next(new Error("Unauthorized"));
        }
    });

    io.on("connection", (socket) => {
        const { userId, role } = socket.data;
        socket.join(userRoom(userId));
        if (role === "recruiter") socket.join(recruiterRoom(userId));
        logger.info("socket connected", { userId, role, sid: socket.id });

        socket.on("disconnect", () => {
            logger.info("socket disconnected", { userId, sid: socket.id });
        });
    });

    return io;
};

const getIO = () => io;

module.exports = { initSocket, getIO, recruiterRoom, userRoom };
