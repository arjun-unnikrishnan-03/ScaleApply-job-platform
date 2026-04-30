const { redis, isReady } = require("../config/redis");
const logger = require("../utils/logger");

const get = async (key) => {
    if (!isReady()) return null;
    try {
        return await redis.get(key);
    } catch (err) {
        logger.warn("cache.get failed", { key, error: err.message });
        return null;
    }
};

const set = async (key, value, ttlSeconds) => {
    if (!isReady()) return;
    try {
        await redis.set(key, value, "EX", ttlSeconds);
    } catch (err) {
        logger.warn("cache.set failed", { key, error: err.message });
    }
};

const acquireLock = async (key, ttlMs) => {
    if (!isReady()) return false;
    try {
        const res = await redis.set(key, "1", "PX", ttlMs, "NX");
        return res === "OK";
    } catch {
        return false;
    }
};

const release = async (key) => {
    if (!isReady()) return;
    try {
        await redis.del(key);
    } catch {
        /* noop */
    }
};

const invalidatePattern = async (pattern) => {
    if (!isReady()) return 0;
    let cursor = "0";
    let total = 0;
    try {
        do {
            const [next, keys] = await redis.scan(cursor, "MATCH", pattern, "COUNT", 200);
            cursor = next;
            if (keys.length) {
                await redis.unlink(...keys);
                total += keys.length;
            }
        } while (cursor !== "0");
    } catch (err) {
        logger.warn("cache.invalidatePattern failed", { pattern, error: err.message });
    }
    return total;
};

module.exports = { get, set, acquireLock, release, invalidatePattern };
