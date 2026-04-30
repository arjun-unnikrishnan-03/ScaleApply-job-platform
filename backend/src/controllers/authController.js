const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const User = require("../models/User");
const env = require("../config/env");
const ApiError = require("../utils/ApiError");
const asyncHandler = require("../utils/asyncHandler");

const signToken = (user) =>
    jwt.sign({ id: user._id.toString(), role: user.role }, env.jwtSecret, { expiresIn: env.jwtExpiresIn });

const register = asyncHandler(async (req, res) => {
    const { email, password, role } = req.body;

    const hashed = await bcrypt.hash(password, 10);
    try {
        const user = await User.create({ email, password: hashed, role });
        return res.status(201).json({ id: user._id, email: user.email, role: user.role });
    } catch (err) {
        // Avoid user enumeration: respond uniformly even on duplicate.
        if (err.code === 11000) {
            return res.status(201).json({ id: null, email, role });
        }
        throw err;
    }
});

const login = asyncHandler(async (req, res) => {
    const { email, password } = req.body;

    const user = await User.findOne({ email });
    if (!user) throw new ApiError(401, "Invalid credentials");

    const ok = await bcrypt.compare(password, user.password);
    if (!ok) throw new ApiError(401, "Invalid credentials");

    return res.json({ token: signToken(user), role: user.role, id: user._id });
});

const me = asyncHandler(async (req, res) => {
    res.json({ id: req.user._id, email: req.user.email, role: req.user.role });
});

module.exports = { register, login, me };
