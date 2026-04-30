const Job = require("../models/Job");
const ApiError = require("../utils/ApiError");
const asyncHandler = require("../utils/asyncHandler");
const escapeRegex = require("../utils/escapeRegex");
const cacheService = require("../services/cacheService");

const invalidateJobsCache = () => cacheService.invalidatePattern("jobs:*");

const createJob = asyncHandler(async (req, res) => {
    const { title, description } = req.body;
    const job = await Job.create({ title, description, recruiterId: req.user._id });
    invalidateJobsCache();
    res.status(201).json(job);
});

const getJobs = asyncHandler(async (req, res) => {
    const { search, page, limit } = req.query;
    const query = {};
    if (search) {
        const safe = escapeRegex(search);
        query.$or = [{ title: { $regex: safe, $options: "i" } }, { description: { $regex: safe, $options: "i" } }];
    }

    const skip = (page - 1) * limit;
    const [total, jobs] = await Promise.all([
        Job.countDocuments(query),
        Job.find(query).populate("recruiterId", "email").sort({ createdAt: -1 }).skip(skip).limit(limit).lean()
    ]);

    res.json({
        jobs,
        currentPage: page,
        totalPages: Math.max(1, Math.ceil(total / limit)),
        totalJobs: total
    });
});

const getMyJobs = asyncHandler(async (req, res) => {
    if (req.user.role !== "recruiter") throw new ApiError(403, "Forbidden");
    const jobs = await Job.find({ recruiterId: req.user._id }).sort({ createdAt: -1 }).lean();
    res.json(jobs);
});

module.exports = { createJob, getJobs, getMyJobs };
