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
        console.error('Error in analyzeResume AI service call:', error?.response?.data || error.message);
        throw new Error(error?.response?.data?.error || 'Failed to analyze resume via AI Service');
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
        console.error('Error in evaluateATS AI service call:', error?.response?.data || error.message);
        throw new Error(error?.response?.data?.error || 'Failed to evaluate ATS via AI Service');
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
        console.error('Error in queryKnowledgeBase AI service call:', error?.response?.data || error.message);
        throw new Error(error?.response?.data?.error || 'Failed to query knowledge base via AI Service');
    }
};

module.exports = {
    aiClient,
    analyzeResume,
    evaluateATS,
    queryKnowledgeBase
};
