const express = require("express");
const router = express.Router();
const { createJob, getJobs } = require("../controllers/jobController");
const { protect } = require("../middleware/authMiddleware");
const cache = require("../middleware/cacheMiddleware");

// Public route to get all jobs (cached)
router.get("/", cache("jobs", 120), getJobs);

// Protected route to get jobs posted by the recruiter
router.get("/me", protect, require("../controllers/jobController").getMyJobs);

// Protected route to create a new job
router.post("/", protect, createJob);

module.exports = router;
