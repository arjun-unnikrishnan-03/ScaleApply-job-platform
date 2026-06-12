const { GoogleGenerativeAI } = require("@google/generative-ai");
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

const callGemini = async (prompt) => {
    const genAI = new GoogleGenerativeAI(env.gemini.apiKey);
    const model = genAI.getGenerativeModel({
        model: "gemini-flash-latest",
        systemInstruction: SYSTEM_PROMPT,
        generationConfig: {
            responseMimeType: "application/json",
            temperature: 0.1,
            maxOutputTokens: 800
        }
    });

    const result = await model.generateContent(prompt);
    return result.response.text();
};

const isConfigured = () => {
    const { apiKey } = env.gemini;
    return Boolean(apiKey && !apiKey.includes("your_key"));
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
            const raw = await callGemini(prompt);
            const parsed = extractJson(raw);
            if (parsed && typeof parsed.score === "number") {
                const score = Math.max(0, Math.min(100, Math.round(parsed.score)));
                return { score, explanation: String(parsed.explanation || "").slice(0, 800) };
            }
            logger.warn("AI returned unparseable response", { sample: String(raw).slice(0, 200) });
        } catch (err) {
            logger.warn("AI call failed", { attempt, error: err.message });
        }
        attempt += 1;
    }

    return { score: null, explanation: "AI scoring temporarily unavailable." };
};

module.exports = { scoreResume };
