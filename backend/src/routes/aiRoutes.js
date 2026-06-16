const express = require("express");
const multer = require("multer");
const { protect, requireRole } = require("../middleware/authMiddleware");
const { autoFillProfile, queryAIKnowledgeBase, recommendJobs } = require("../controllers/aiController");

const router = express.Router();

const memoryUpload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: 5 * 1024 * 1024 }
});

// Candidate: Upload a resume to auto-fill their profile via AI
router.post(
    "/resume/analyze",
    protect,
    requireRole("candidate"),
    memoryUpload.single("resume"),
    autoFillProfile
);

// Global: Query the RAG knowledge base for answers
router.post(
    "/knowledge/query",
    protect,
    queryAIKnowledgeBase
);

// Candidate: Get job recommendations based on saved profile
router.get(
    "/recommendations",
    protect,
    requireRole("candidate"),
    recommendJobs
);

module.exports = router;
