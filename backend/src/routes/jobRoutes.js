const express = require("express");
const validate = require("../middleware/validate");
const cache = require("../middleware/cacheMiddleware");
const { protect, requireRole } = require("../middleware/authMiddleware");
const { createJob, getJobs, getMyJobs } = require("../controllers/jobController");
const { createJobSchema, listJobsQuerySchema } = require("../validators/jobValidators");

const router = express.Router();

router.get("/", validate(listJobsQuerySchema, "query"), cache("jobs", 120), getJobs);
router.get("/me", protect, requireRole("recruiter"), getMyJobs);
router.post("/", protect, requireRole("recruiter"), validate(createJobSchema), createJob);

module.exports = router;
