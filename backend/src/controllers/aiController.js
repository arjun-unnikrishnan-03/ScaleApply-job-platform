const { analyzeResume, evaluateATS, queryKnowledgeBase } = require("../services/aiClient");
const { parseResume } = require("../services/resumeParser");
const User = require("../models/User");
const Application = require("../models/Application");
const Job = require("../models/Job");
const logger = require("../utils/logger");

/**
 * Uploads a resume, parses text, calls AI Service to extract candidate profile,
 * and saves it to the User's record.
 */
const autoFillProfile = async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: "No resume file uploaded." });
        }

        // 1. Parse text from buffer
        const { text, kind } = await parseResume(req.file.buffer, req.file.originalname);
        
        if (!text || text.length < 50) {
            return res.status(400).json({ error: "Could not extract sufficient text from the document." });
        }

        // 2. Call FastAPI AI Service (returns raw profile)
        const profile = await analyzeResume(text);

        // 3. Map profile to front-end expected structure
        const mappedProfile = {
            contact_info: {
                name: profile.full_name || "",
                email: profile.email || ""
            },
            summary: profile.professional_summary || "",
            skills: {
                technical: profile.technical_skills || []
            },
            experience: (profile.experience || []).map(exp => ({
                title: exp.title || "",
                company: exp.company || "",
                start_date: exp.duration?.start_date || "",
                end_date: exp.duration?.end_date || "Present",
                highlights: exp.responsibilities || []
            })),
            education: (profile.education || []).map(edu => ({
                degree: edu.degree || "",
                institution: edu.institution || "",
                graduation_date: edu.graduation_year ? String(edu.graduation_year) : ""
            }))
        };

        // 4. Save to User Model
        const updatedUser = await User.findByIdAndUpdate(
            req.user._id, // From protect middleware
            { candidateProfile: mappedProfile },
            { new: true, runValidators: false }
        );

        if (!updatedUser) {
            return res.status(404).json({ error: "User not found." });
        }

        logger.info(`AI Resume parsed successfully for user ${req.user.userId}`);
        
        return res.status(200).json({
            message: "Profile auto-filled successfully",
            profile: updatedUser.candidateProfile
        });

    } catch (error) {
        logger.error("Error in autoFillProfile:", error);
        return res.status(500).json({ error: error.message || "Failed to process resume via AI." });
    }
};

/**
 * Queries the AI RAG Knowledge Base and returns context/answers.
 */
const queryAIKnowledgeBase = async (req, res) => {
    try {
        const { query, limit } = req.body;
        if (!query || typeof query !== "string") {
            return res.status(400).json({ error: "Query string is required." });
        }

        const result = await queryKnowledgeBase(query, limit || 3);
        return res.status(200).json(result);
    } catch (error) {
        logger.error("Error in queryAIKnowledgeBase:", error);
        return res.status(500).json({ error: error.message || "Failed to query AI Knowledge Base." });
    }
};

module.exports = {
    autoFillProfile,
    queryAIKnowledgeBase
};
