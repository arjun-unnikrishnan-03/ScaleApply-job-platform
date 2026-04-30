const redis = require("../config/redis");

const cache = (prefix, ttl) => {
    return async (req, res, next) => {
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
                res.setHeader("Content-Type", "application/json");
                return res.send(cachedData);
            }

            console.log(`[Cache Miss] ${key}`);
            res.setHeader("X-Cache", "MISS");

            const acquiredLock = await redis.set(lockKey, "1", "PX", 2000, "NX");
            
            const originalJson = res.json.bind(res);
            res.json = (body) => {
                if (acquiredLock) {
                    try {
                        const jsonString = JSON.stringify(body);
                        redis.set(key, jsonString, "EX", ttl).then(() => {
                            console.log(`[Cache Set] ${key}`);
                            redis.del(lockKey);
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
            next();
        }
    };
};

module.exports = cache;
