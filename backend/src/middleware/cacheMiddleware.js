const cacheService = require("../services/cacheService");

const buildKey = (prefix, req) => {
    const url = new URL(req.originalUrl, "http://x");
    const params = [...url.searchParams.entries()].sort(([a], [b]) => a.localeCompare(b));
    const query = params.map(([k, v]) => `${k}=${v}`).join("&");
    return `${prefix}:${url.pathname}${query ? `?${query}` : ""}`;
};

const cache = (prefix, ttlSeconds) => async (req, res, next) => {
    const key = buildKey(prefix, req);
    const lockKey = `lock:${key}`;

    const cached = await cacheService.get(key);
    if (cached) {
        res.setHeader("X-Cache", "HIT");
        res.setHeader("Content-Type", "application/json");
        return res.send(cached);
    }
    res.setHeader("X-Cache", "MISS");

    const acquired = await cacheService.acquireLock(lockKey, 2000);
    const originalJson = res.json.bind(res);
    res.json = (body) => {
        if (acquired && res.statusCode >= 200 && res.statusCode < 300) {
            const payload = JSON.stringify(body);
            cacheService
                .set(key, payload, ttlSeconds)
                .finally(() => cacheService.release(lockKey));
        } else if (acquired) {
            cacheService.release(lockKey);
        }
        return originalJson(body);
    };
    next();
};

module.exports = cache;
