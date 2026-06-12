const Application = require("../models/Application");
const Job = require("../models/Job");
const ApiError = require("../utils/ApiError");
const logger = require("../utils/logger");
const { parseResume } = require("./resumeParser");
const { scoreResume } = require("./aiService");
const { getFileBuffer } = require("./s3Service");
const { notifyRecruiterNewApplication, notifyCandidateScored } = require("./notificationService");

const createApplication = async ({ userId, jobId, file }) => {
    const job = await Job.findById(jobId).lean();
    if (!job) throw new ApiError(404, "Job not found");
    if (!file) throw new ApiError(400, "Resume file is required");

    let application;
    try {
        application = await Application.create({
            userId,
            jobId,
            resumeKey: file.key,
            resumeOriginalName: file.originalname
        });
    } catch (err) {
        if (err && err.code === 11000) throw new ApiError(409, "You have already applied for this job");
        throw err;
    }

    notifyRecruiterNewApplication(job.recruiterId.toString(), {
        applicationId: application._id,
        jobId: job._id,
        jobTitle: job.title,
        appliedAt: application.createdAt
    });

    scoreApplicationAsync(application._id).catch((err) =>
        logger.warn("scoreApplicationAsync failed", { applicationId: application._id.toString(), error: err.message })
    );

    return application;
};

const scoreApplicationAsync = async (applicationId) => {
    const application = await Application.findById(applicationId);
    if (!application) return;
    const job = await Job.findById(application.jobId).lean();
    if (!job) return;

    let resumeText = "";
    try {
        const buffer = await getFileBuffer(application.resumeKey);
        const parsed = await parseResume(buffer, application.resumeOriginalName);
        resumeText = parsed.text;
    } catch (err) {
        logger.warn("Resume fetch/parse failed", { applicationId: applicationId.toString(), error: err.message });
    }

    const { score, explanation } = await scoreResume({
        resumeText,
        jobTitle: job.title,
        jobDescription: job.description
    });

    application.score = score;
    application.explanation = explanation;
    application.scoredAt = new Date();
    await application.save();

    notifyCandidateScored(application.userId.toString(), {
        applicationId: application._id,
        jobId: job._id,
        score,
        explanation
    });
    notifyRecruiterNewApplication(job.recruiterId.toString(), {
        type: "scored",
        applicationId: application._id,
        jobId: job._id,
        score
    });
};

module.exports = { createApplication, scoreApplicationAsync };
