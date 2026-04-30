const express = require("express");
const router = express.Router();
const { applyToJob, getApplicationsForJob } = require("../controllers/applicationController");
const { protect } = require("../middleware/authMiddleware");
const upload = require("../middleware/uploadMiddleware");

// Protected route to apply to a job with resume upload
router.post("/:jobId", protect, upload.single("resume"), applyToJob);

// Protected route to get applications for a specific job (Recruiter only)
router.get("/job/:jobId", protect, getApplicationsForJob);

module.exports = router;
