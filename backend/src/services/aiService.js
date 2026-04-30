const axios = require("axios");
const env = require("../config/env");
const logger = require("../utils/logger");

const SYSTEM_PROMPT = `You are an expert technical recruiter scoring how well a candidate's resume matches a job description.
Return ONLY a JSON object: {"score": <integer 0-100>, "explanation": "<2-3 concise sentences citing concrete strengths and gaps>"}.
Scoring rubric: 90-100 = strong match across required skills and seniority; 70-89 = solid match with minor gaps; 50-69 = partial match with notable gaps; 30-49 = weak match; 0-29 = mismatch.
Do not invent skills. If the resume text is empty or clearly insufficient, return score 0 with an explanation that the resume could not be evaluated.`;

const extractJson = (raw) => {
    if (!raw) return null;
    const cleaned = raw.replace(/```(?:json)?/g, "").trim();
    const start = cleaned.indexOf("{");
    const end = cleaned.lastIndexOf("}");
    if (start === -1 || end === -1) return null;
    try {
        return JSON.parse(cleaned.slice(start, end + 1));
    } catch {
        return null;
    }
};

const callAzure = async (prompt) => {
    const { endpoint, key } = env.azureOpenAI;
    const response = await axios.post(
        endpoint,
        {
            messages: [
                { role: "system", content: SYSTEM_PROMPT },
                { role: "user", content: prompt }
            ],
            temperature: 0.1,
            max_tokens: 400,
            response_format: { type: "json_object" }
        },
        {
            headers: { "Content-Type": "application/json", "api-key": key },
            timeout: 20000
        }
    );
    return response.data?.choices?.[0]?.message?.content;
};

const isConfigured = () => {
    const { endpoint, key } = env.azureOpenAI;
    return Boolean(endpoint && key && key !== "your_key");
};

const scoreResume = async ({ resumeText, jobTitle, jobDescription }) => {
    if (!isConfigured()) {
        return { score: null, explanation: "AI scoring is not configured." };
    }

    if (!resumeText || resumeText.trim().length < 40) {
        return { score: 0, explanation: "Resume text could not be extracted or is too short to evaluate." };
    }

    const prompt = `JOB TITLE:\n${jobTitle}\n\nJOB DESCRIPTION:\n${jobDescription}\n\nRESUME:\n${resumeText}`;

    let attempt = 0;
    while (attempt < 2) {
        try {
            const raw = await callAzure(prompt);
            const parsed = extractJson(raw);
            if (parsed && typeof parsed.score === "number") {
                const score = Math.max(0, Math.min(100, Math.round(parsed.score)));
                return { score, explanation: String(parsed.explanation || "").slice(0, 800) };
            }
            logger.warn("AI returned unparseable response", { sample: String(raw).slice(0, 200) });
        } catch (err) {
            logger.warn("AI call failed", { attempt, error: err.response?.data || err.message });
        }
        attempt += 1;
    }

    return { score: null, explanation: "AI scoring temporarily unavailable." };
};

module.exports = { scoreResume };
