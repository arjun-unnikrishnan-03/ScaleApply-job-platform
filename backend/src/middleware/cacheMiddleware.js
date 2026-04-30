const redis = require("../config/redis");

const cache = (prefix, ttl) => {
    return async (req, res, next) => {
        // Fail-Safe: If Redis is down, completely bypass the cache
        if (redis.status !== "ready") {
            return next();
        }

        const key = `${prefix}:${req.originalUrl}`;
        const lockKey = `lock:${key}`;

        try {
            const cachedData = await redis.get(key);

            if (cachedData) {
                console.log(`[Cache Hit] ${key}`);
                res.setHeader("X-Cache", "HIT");
                
                // Serialization optimization: Send raw JSON string directly
                res.setHeader("Content-Type", "application/json");
                return res.send(cachedData);
            }

            console.log(`[Cache Miss] ${key}`);
            res.setHeader("X-Cache", "MISS");

            // Cache Stampede Protection: Try to acquire a short-lived lock
            const acquiredLock = await redis.set(lockKey, "1", "PX", 2000, "NX");
            
            // Override res.json to capture and cache the response
            const originalJson = res.json.bind(res);
            res.json = (body) => {
                if (acquiredLock) {
                    try {
                        const jsonString = JSON.stringify(body);
                        redis.set(key, jsonString, "EX", ttl).then(() => {
                            console.log(`[Cache Set] ${key}`);
                            redis.del(lockKey); // Release lock
                        });
                    } catch (e) {
                        console.error("Cache serialization error:", e.message);
                    }
                }
                return originalJson(body);
            };

            next();
        } catch (error) {
            console.error("Cache Middleware Error:", error.message);
            // Fail open: Fallback to original DB request if cache errors out
            next();
        }
    };
};

module.exports = cache;
