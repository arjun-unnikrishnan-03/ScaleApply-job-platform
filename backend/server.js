require("dotenv").config();
const http = require("http");
const app = require("./src/app");
const env = require("./src/config/env");
const connectDB = require("./src/config/db");
const logger = require("./src/utils/logger");
const { initSocket } = require("./src/socket");

const start = async () => {
    await connectDB();

    const server = http.createServer(app);
    initSocket(server);

    server.listen(env.port, () => logger.info(`Server listening on port ${env.port}`, { env: env.nodeEnv }));

    const shutdown = (signal) => {
        logger.info(`${signal} received, shutting down`);
        server.close(() => process.exit(0));
        setTimeout(() => process.exit(1), 10000).unref();
    };
    process.on("SIGINT", () => shutdown("SIGINT"));
    process.on("SIGTERM", () => shutdown("SIGTERM"));
};

start().catch((err) => {
    logger.error("Failed to start server", { error: err.message });
    process.exit(1);
});
