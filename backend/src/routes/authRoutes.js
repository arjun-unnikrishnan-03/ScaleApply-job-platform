const express = require("express");
const rateLimit = require("express-rate-limit");
const validate = require("../middleware/validate");
const { protect } = require("../middleware/authMiddleware");
const { register, login, me } = require("../controllers/authController");
const { registerSchema, loginSchema } = require("../validators/authValidators");

const router = express.Router();

const loginLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 10,
    message: { message: "Too many login attempts. Try again in 15 minutes." }
});

router.post("/register", validate(registerSchema), register);
router.post("/login", loginLimiter, validate(loginSchema), login);
router.get("/me", protect, me);

module.exports = router;
