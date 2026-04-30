const Job = require("../models/Job");

// @desc    Create a new job
// @route   POST /api/jobs
// @access  Private (Recruiters only)
const createJob = async (req, res) => {
    try {
        const { title, description } = req.body;

        if (!title || !description) {
            return res.status(400).json({ message: "Please provide title and description" });
        }

        const existingJob = await Job.findOne({
            recruiterId: req.user._id,
            title,
            description
        });

        if (existingJob) {
            return res.status(400).json({ message: "You have already posted an identical job" });
        }

        const job = await Job.create({
            title,
            description,
            recruiterId: req.user._id
        });

        try {
            const redis = require("../config/redis");
            if (redis.status === "ready") {
                const keys = await redis.keys("jobs:*");
                if (keys.length > 0) {
                    await redis.del(keys);
                    console.log(`[Cache Invalidation] Deleted ${keys.length} keys for pattern 'jobs:*'`);
                }
            }
        } catch (redisError) {
            console.error("Cache Invalidation Error:", redisError.message);
        }

        res.status(201).json(job);
    } catch (error) {
        console.error(error);
        res.status(500).json({ message: "Server Error: Could not create job" });
    }
};

// @desc    Get all jobs
// @route   GET /api/jobs
const getJobs = async (req, res) => {
    try {
        const { search, page = 1, limit = 9 } = req.query;
        let query = {};
        
        if (search) {
            query = {
                $or: [
                    { title: { $regex: search, $options: "i" } },
                    { description: { $regex: search, $options: "i" } }
                ]
            };
        }

        const pageNum = parseInt(page);
        const limitNum = parseInt(limit);
        const skip = (pageNum - 1) * limitNum;

        const total = await Job.countDocuments(query);
        
        const jobs = await Job.find(query)
            .populate("recruiterId", "email")
            .sort({ createdAt: -1 })
            .skip(skip)
            .limit(limitNum);

        res.status(200).json({
            jobs,
            currentPage: pageNum,
            totalPages: Math.ceil(total / limitNum),
            totalJobs: total
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({ message: "Server Error: Could not fetch jobs" });
    }
};

// @desc    Get jobs posted by recruiter
// @route   GET /api/jobs/me
// @access  Private (Recruiters only)
const getMyJobs = async (req, res) => {
    try {
        const jobs = await Job.find({ recruiterId: req.user._id }).sort({ createdAt: -1 });
        res.status(200).json(jobs);
    } catch (error) {
        console.error("Error fetching recruiter jobs:", error);
        res.status(500).json({ message: "Server Error: Could not fetch jobs" });
    }
};

module.exports = {
    createJob,
    getJobs,
    getMyJobs
};
