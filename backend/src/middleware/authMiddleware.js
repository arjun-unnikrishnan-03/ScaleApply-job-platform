const jwt = require("jsonwebtoken");
const User = require("../models/User");
const env = require("../config/env");
const ApiError = require("../utils/ApiError");
const asyncHandler = require("../utils/asyncHandler");

const protect = asyncHandler(async (req, _res, next) => {
    const header = req.headers.authorization;
    if (!header || !header.startsWith("Bearer ")) {
        throw new ApiError(401, "Not authorized, no token");
    }

    const token = header.slice(7);
    let decoded;
    try {
        decoded = jwt.verify(token, env.jwtSecret);
    } catch {
        throw new ApiError(401, "Not authorized, token invalid or expired");
    }

    const user = await User.findById(decoded.id).select("-password").lean();
    if (!user) throw new ApiError(401, "Not authorized, user not found");

    req.user = user;
    next();
});

const requireRole = (...roles) => (req, _res, next) => {
    if (!req.user || !roles.includes(req.user.role)) {
        return next(new ApiError(403, "Forbidden"));
    }
    next();
};

module.exports = { protect, requireRole };
