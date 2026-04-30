const Redis = require("ioredis");

const redis = new Redis({
    host: process.env.REDIS_HOST || "127.0.0.1",
    port: process.env.REDIS_PORT || 6379,
    // Add retry strategy with exponential backoff (stop after 3 tries)
    retryStrategy(times) {
        if (times > 3) {
            console.warn("Redis is not running locally. Disabling cache and falling back to MongoDB.");
            return null; // Stops retrying and prevents console spam
        }
        const delay = Math.min(times * 50, 2000);
        return delay;
    },
    // Prevent hanging forever if Redis is down
    maxRetriesPerRequest: 3 
});

redis.on("connect", () => {
    console.log("Redis Connected Successfully");
});

redis.on("error", (err) => {
    console.error("Redis Connection Error:", err.message);
});

module.exports = redis;
