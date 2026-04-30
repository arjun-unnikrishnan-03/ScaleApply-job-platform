const express = require("express");
const rateLimit = require("express-rate-limit");
const validate = require("../middleware/validate");
const { protect, requireRole } = require("../middleware/authMiddleware");
const upload = require("../middleware/uploadMiddleware");
const { apply, listApplicationsForJob, myApplications } = require("../controllers/applicationController");
const { jobIdParamSchema } = require("../validators/jobValidators");

const router = express.Router();

const applyLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 10,
    message: { message: "Too many applications submitted. Try again in 15 minutes." }
});

router.post(
    "/:jobId",
    protect,
    requireRole("candidate"),
    applyLimiter,
    validate(jobIdParamSchema, "params"),
    upload.single("resume"),
    apply
);

router.get("/me", protect, requireRole("candidate"), myApplications);
router.get("/job/:jobId", protect, requireRole("recruiter"), validate(jobIdParamSchema, "params"), listApplicationsForJob);

module.exports = router;
