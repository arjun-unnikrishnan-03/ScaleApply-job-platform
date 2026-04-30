const Redis = require("ioredis");
const env = require("./env");
const logger = require("../utils/logger");

const redis = new Redis({
    host: env.redis.host,
    port: env.redis.port,
    password: env.redis.password,
    lazyConnect: false,
    enableOfflineQueue: false,
    maxRetriesPerRequest: 2,
    retryStrategy(times) {
        if (times > 3) {
            logger.warn("Redis unreachable; cache disabled, fallback to MongoDB");
            return null;
        }
        return Math.min(times * 100, 1000);
    }
});

redis.on("connect", () => logger.info("Redis connected"));
redis.on("error", (err) => logger.error("Redis error", { error: err.message }));

const isReady = () => redis.status === "ready";

module.exports = { redis, isReady };
