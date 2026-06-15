const Application = require("../models/Application");
const Job = require("../models/Job");
const ApiError = require("../utils/ApiError");
const logger = require("../utils/logger");
const { parseResume } = require("./resumeParser");
const { analyzeResume, evaluateATS } = require("./aiClient");
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
        return;
    }

    try {
        // 1. Parse raw text into structured CandidateProfile via AI Service
        const candidateProfile = await analyzeResume(resumeText);

        // 2. Map Mongoose Job to FastAPI JobDescription schema
        const jobDescription = {
            title: job.title,
            company_name: "ScaleApply Client",
            summary: job.description || "",
            required_skills: job.title.split(/[\s,/-]+/).filter(w => w.length > 2 && !/^(and|for|with|the)$/i.test(w)) || ["Software"],
            preferred_skills: [],
            technologies: [],
            responsibilities: [],
            qualifications: []
        };

        // 3. Evaluate ATS Match via AI Service
        const atsResult = await evaluateATS(candidateProfile, jobDescription);

        // 4. Update Application model with new structured AI fields
        if (atsResult && atsResult.ats_result) {
            application.atsResult = atsResult.ats_result;
            application.score = atsResult.ats_result.score;
            application.explanation = atsResult.ats_result.explanation;
            application.skillGapAnalysis = atsResult.ats_result.missing_skills;
            application.scoredAt = new Date();
            await application.save();

            notifyCandidateScored(application.userId.toString(), {
                applicationId: application._id,
                jobId: job._id,
                score: atsResult.ats_result.score,
                explanation: atsResult.ats_result.explanation
            });
            notifyRecruiterNewApplication(job.recruiterId.toString(), {
                type: "scored",
                applicationId: application._id,
                jobId: job._id,
                score: atsResult.ats_result.score
            });
        }
        
    } catch (err) {
        logger.error("FastAPI AI Service ATS evaluation failed", { applicationId: applicationId.toString(), error: err.message });
    }
};

module.exports = { createApplication, scoreApplicationAsync };
