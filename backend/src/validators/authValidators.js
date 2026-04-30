const { z } = require("zod");

const registerSchema = z.object({
    email: z.string().trim().toLowerCase().email(),
    password: z.string().min(8).max(128),
    role: z.enum(["recruiter", "candidate"])
});

const loginSchema = z.object({
    email: z.string().trim().toLowerCase().email(),
    password: z.string().min(1).max(128)
});

module.exports = { registerSchema, loginSchema };
