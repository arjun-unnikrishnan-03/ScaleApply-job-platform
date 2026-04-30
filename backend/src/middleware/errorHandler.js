const logger = require("../utils/logger");
const ApiError = require("../utils/ApiError");

const errorHandler = (err, req, res, _next) => {
    if (err instanceof ApiError) {
        return res.status(err.status).json({
            message: err.message,
            ...(err.details ? { details: err.details } : {})
        });
    }

    if (err && err.name === "ValidationError") {
        return res.status(400).json({ message: "Validation failed", details: err.errors });
    }

    if (err && err.code === 11000) {
        return res.status(409).json({ message: "Duplicate resource" });
    }

    if (err && err.message && err.message.startsWith("Error: Only PDF, DOC")) {
        return res.status(415).json({ message: err.message.replace(/^Error:\s*/, "") });
    }

    logger.error("Unhandled error", { path: req.originalUrl, error: err && err.message, stack: err && err.stack });
    return res.status(500).json({ message: "Internal server error" });
};

const notFound = (req, res) => res.status(404).json({ message: `Route not found: ${req.method} ${req.originalUrl}` });

module.exports = { errorHandler, notFound };
