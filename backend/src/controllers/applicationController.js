const Application = require("../models/Application");
const Job = require("../models/Job");
const ApiError = require("../utils/ApiError");
const asyncHandler = require("../utils/asyncHandler");
const logger = require("../utils/logger");
const applicationService = require("../services/applicationService");
const { getSignedDownloadUrl } = require("../services/s3Service");

const apply = asyncHandler(async (req, res) => {
    if (req.user.role !== "candidate") throw new ApiError(403, "Only candidates can apply");
    const application = await applicationService.createApplication({
        userId: req.user._id,
        jobId: req.params.jobId,
        file: req.file
    });
    res.status(202).json({
        id: application._id,
        status: "queued",
        message: "Application received. Match score will be ready shortly."
    });
});

const listApplicationsForJob = asyncHandler(async (req, res) => {
    if (req.user.role !== "recruiter") throw new ApiError(403, "Forbidden");
    const job = await Job.findById(req.params.jobId).lean();
    if (!job) throw new ApiError(404, "Job not found");
    if (job.recruiterId.toString() !== req.user._id.toString()) throw new ApiError(403, "Forbidden");

    const applications = await Application.find({ jobId: job._id })
        .populate("userId", "email")
        .sort({ score: -1, createdAt: -1 })
        .lean();

    const enriched = await Promise.all(
        applications.map(async (app) => {
            const ref = app.resumeKey || app.resumeUrl;
            let resumeUrl = null;
            if (ref) {
                try {
                    resumeUrl = await getSignedDownloadUrl(ref);
                } catch (err) {
                    logger.warn("presigned url failed", { applicationId: app._id.toString(), error: err.message });
                }
            }
            return { ...app, resumeUrl };
        })
    );

    res.json(enriched);
});

const myApplications = asyncHandler(async (req, res) => {
    if (req.user.role !== "candidate") throw new ApiError(403, "Forbidden");
    const applications = await Application.find({ userId: req.user._id })
        .populate("jobId", "title")
        .sort({ createdAt: -1 })
        .lean();
    res.json(applications);
});

module.exports = { apply, listApplicationsForJob, myApplications };
