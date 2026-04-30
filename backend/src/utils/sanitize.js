const FORBIDDEN_KEY = /^\$|\./;

const sanitizeInPlace = (value) => {
    if (value === null || typeof value !== "object") return value;

    if (Array.isArray(value)) {
        for (const item of value) sanitizeInPlace(item);
        return value;
    }

    for (const key of Object.keys(value)) {
        if (FORBIDDEN_KEY.test(key)) {
            delete value[key];
            continue;
        }
        sanitizeInPlace(value[key]);
    }
    return value;
};

const sanitizeRequest = (req, _res, next) => {
    if (req.body) sanitizeInPlace(req.body);
    if (req.params) sanitizeInPlace(req.params);
    next();
};

module.exports = { sanitizeRequest, sanitizeInPlace };
