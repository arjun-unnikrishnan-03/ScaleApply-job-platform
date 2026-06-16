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
        
        // FastAPI returns { query, documents: [{content, sources}], scores }
        // Extract the main answer from the first document
        const answer = result?.documents?.[0]?.content 
            || result?.answer 
            || "I couldn't find a specific answer in my knowledge base. Try asking about job roles, skills, or interview prep!";
        
        const sources = result?.documents?.[0]?.sources || [];
        
        return res.status(200).json({ answer, sources });
    } catch (error) {
        logger.error("Error in queryAIKnowledgeBase:", error);
        return res.status(500).json({ error: error.message || "Failed to query AI Knowledge Base." });
    }
};

/**
 * Recommends suitable jobs based on user's saved candidate profile.
 */
const recommendJobs = async (req, res) => {
    try {
        const user = await User.findById(req.user._id).lean();
        if (!user?.candidateProfile) {
            return res.status(400).json({ error: "No candidate profile found. Please upload your resume first." });
        }

        const profile = user.candidateProfile;
        const skills = profile.skills?.technical || [];
        const experience = profile.experience || [];

        // Build a query from the candidate's skills and latest job title
        const latestRole = experience[0]?.title || "";
        const skillString = skills.slice(0, 8).join(", ");

        // Search jobs in MongoDB using text match on skills / title
        const jobs = await Job.find({
            $or: [
                { title: { $regex: skills.slice(0, 3).join("|"), $options: "i" } },
                { description: { $regex: skills.slice(0, 5).join("|"), $options: "i" } }
            ]
        })
        .sort({ createdAt: -1 })
        .limit(5)
        .lean();

        // If no regex match, just return latest 5 jobs
        const fallbackJobs = jobs.length > 0 ? jobs : await Job.find({}).sort({ createdAt: -1 }).limit(5).lean();

        // Get jobs user already applied to
        const applications = await Application.find({ userId: req.user._id }).select("jobId").lean();
        const appliedJobIds = new Set(applications.map(a => a.jobId.toString()));

        const recommended = fallbackJobs.map(job => ({
            _id: job._id,
            title: job.title,
            company: job.company || "Company",
            description: job.description?.substring(0, 150) + "...",
            location: job.location || "Remote",
            alreadyApplied: appliedJobIds.has(job._id.toString()),
            matchedSkills: skills.filter(s => 
                job.title?.toLowerCase().includes(s.toLowerCase()) || 
                job.description?.toLowerCase().includes(s.toLowerCase())
            ).slice(0, 4)
        }));

        return res.status(200).json({
            profile: { name: profile.contact_info?.name, skills: skills.slice(0, 6), latestRole },
            recommendations: recommended
        });
    } catch (error) {
        logger.error("Error in recommendJobs:", error);
        return res.status(500).json({ error: "Failed to generate job recommendations." });
    }
};

module.exports = {
    autoFillProfile,
    queryAIKnowledgeBase,
    recommendJobs
};
