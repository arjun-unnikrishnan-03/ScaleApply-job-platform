const express = require("express");
const router = express.Router();
const { applyToJob, getApplicationsForJob } = require("../controllers/applicationController");
const { protect } = require("../middleware/authMiddleware");
const upload = require("../middleware/uploadMiddleware");

const rateLimit = require("express-rate-limit");

const applicationLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 5, // Limit each IP to 5 applications per 15 minutes to protect AWS S3/Azure OpenAI costs
    message: { message: "Too many applications submitted from this IP, please try again after 15 minutes" }
});

// Protected route to apply to a job with resume upload (Strict Rate Limit)
router.post("/:jobId", protect, applicationLimiter, upload.single("resume"), applyToJob);

// Protected route to get applications for a specific job (Recruiter only)
router.get("/job/:jobId", protect, getApplicationsForJob);

module.exports = router;
