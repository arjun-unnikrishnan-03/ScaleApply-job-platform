const Application = require("../models/Application");
const Job = require("../models/Job");

// @desc    Apply to a job
// @route   POST /api/applications/:jobId
// @access  Private
const applyToJob = async (req, res) => {
    try {
        const { jobId } = req.params;
        const userId = req.user._id;

        const jobExists = await Job.findById(jobId);
        if (!jobExists) {
            return res.status(404).json({ message: "Job not found" });
        }

        if (!req.file) {
            return res.status(400).json({ message: "Please upload a resume (PDF/DOC/DOCX)" });
        }

        const existingApplication = await Application.findOne({ userId, jobId });
        if (existingApplication) {
            return res.status(400).json({ message: "You have already applied for this job" });
        }

        let application = await Application.create({
            userId,
            jobId,
            resumeUrl: req.file.location
        });

        try {
            const { scoreResume } = require("../services/aiService");
            const { getFileBufferFromS3 } = require("../services/s3Service");
            const pdfParse = require("pdf-parse");
            
            let resumeText = "Resume parsing failed";
            
            if (req.file.originalname.toLowerCase().endsWith(".pdf")) {
                try {
                    const fileBuffer = await getFileBufferFromS3(req.file.location);
                    const pdfData = await pdfParse(fileBuffer);
                    if (pdfData.text) {
                        resumeText = pdfData.text.slice(0, 3000);
                    }
                } catch (parseError) {
                    console.error("PDF Parsing Error:", parseError.message);
                }
            } else {
                resumeText = `Candidate submitted a DOC/DOCX file. Filename: ${req.file.originalname}`;
            }

            const jobDescription = jobExists.description;

            const aiResult = await scoreResume(resumeText, jobDescription);
            
            if (aiResult.score !== null) {
                application.score = aiResult.score;
                application.explanation = aiResult.explanation;
                await application.save();
            }
        } catch (aiError) {
            console.error("Non-fatal AI Error:", aiError.message);
        }

        try {
            const io = req.app.get("io");
            if (io) {
                io.emit("new_application", {
                    jobId,
                    userId,
                    message: "New candidate applied"
                });
            }
        } catch (socketError) {
            console.error("Socket emit failed:", socketError.message);
        }

        res.status(201).json(application);
    } catch (error) {
        console.error(error);
        res.status(500).json({ message: "Server Error: Could not process application" });
    }
};

// @desc    Get all applications for a specific job
// @route   GET /api/applications/job/:jobId
// @access  Private (Recruiter only)
const getApplicationsForJob = async (req, res) => {
    try {
        if (req.user.role !== "recruiter") {
            return res.status(403).json({ message: "Access denied" });
        }

        const { jobId } = req.params;
        
        const job = await Job.findById(jobId);
        if (!job) return res.status(404).json({ message: "Job not found" });
        if (job.recruiterId.toString() !== req.user._id.toString()) {
            return res.status(403).json({ message: "Not authorized to view these applications" });
        }

        const applications = await Application.find({ jobId })
            .populate("userId", "email")
            .sort({ score: -1 });

        res.status(200).json(applications);
    } catch (error) {
        console.error("Error fetching applications:", error);
        res.status(500).json({ message: "Server Error" });
    }
};

module.exports = {
    applyToJob,
    getApplicationsForJob
};
