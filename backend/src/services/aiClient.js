const axios = require('axios');

// Default to localhost:8000 if not set in .env
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';

const aiClient = axios.create({
    baseURL: AI_SERVICE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    // Set a high timeout because LLM generation can take 10-30 seconds
    timeout: 60000, 
});

/**
 * Extracts structured data from raw resume text
 * @param {string} resumeText 
 * @returns {Promise<Object>} The CandidateProfile object
 */
const analyzeResume = async (resumeText) => {
    try {
        const response = await aiClient.post('/resume/analyze', { text: resumeText });
        return response.data.profile;
    } catch (error) {
        console.warn('AI quota exhausted or service unavailable. Returning MOCK Profile data.');
        return {
            contact_info: { name: "Mock Candidate (AI Quota Exhausted)", email: "mock@scaleapply.com" },
            summary: "Highly skilled Software Engineer with experience in building scalable web applications. This is a mock profile generated because the AI API quota is currently exhausted.",
            skills: { technical: ["JavaScript", "Python", "React", "Node.js", "Docker"] },
            experience: [
                { title: "Senior Developer", company: "Tech Corp", start_date: "2020", end_date: "Present", highlights: ["Led a team of 5", "Improved performance by 30%"] }
            ],
            education: [
                { degree: "B.S. Computer Science", institution: "State University", graduation_date: "2018" }
            ]
        };
    }
};

/**
 * Evaluates a candidate against a job description
 * @param {Object} candidateProfile CandidateProfile object
 * @param {Object} jobDescription JobDescription object
 * @returns {Promise<Object>} The ATSResult object
 */
const evaluateATS = async (candidateProfile, jobDescription) => {
    try {
        const response = await aiClient.post('/ats/analyze', { 
            candidate_profile: candidateProfile, 
            job_description: jobDescription 
        });
        return response.data;
    } catch (error) {
        console.warn('AI quota exhausted. Returning MOCK ATS Result.');
        return {
            ats_result: {
                score: 75.5,
                explanation: "[MOCK RESPONSE - AI Quota Exhausted] The candidate matches the core engineering requirements well but lacks specific domain experience mentioned in the job description.",
                missing_skills: ["GraphQL", "Kubernetes", "Real API Key"]
            }
        };
    }
};

/**
 * Queries the RAG knowledge base using the KnowledgeAgent
 * @param {string} query The natural language query
 * @param {number} limit Maximum number of documents to retrieve
 * @returns {Promise<Object>} The query result and sources
 */
const queryKnowledgeBase = async (query, limit = 3) => {
    try {
        const response = await aiClient.post('/knowledge/query', { query, limit });
        return response.data;
    } catch (error) {
        console.warn('AI quota exhausted. Returning MOCK Knowledge Result.');
        return {
            answer: "🤖 [MOCK RESPONSE] My AI provider quota is currently exhausted, so I cannot search the knowledge base right now. Please try again later when the quota resets!",
            sources: []
        };
    }
};

module.exports = {
    aiClient,
    analyzeResume,
    evaluateATS,
    queryKnowledgeBase
};
