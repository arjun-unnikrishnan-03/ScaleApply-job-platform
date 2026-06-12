require('dotenv').config();
const { GoogleGenerativeAI } = require('@google/generative-ai');

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

const SYSTEM_PROMPT = `You are an expert technical recruiter scoring how well a candidate's resume matches a job description.
Return ONLY a JSON object: {"score": <integer 0-100>, "explanation": "<2-3 concise sentences citing concrete strengths and gaps>"}.
Scoring rubric: 90-100 = strong match across required skills and seniority; 70-89 = solid match with minor gaps; 50-69 = partial match with notable gaps; 30-49 = weak match; 0-29 = mismatch.
Do not invent skills. If the resume text is empty or clearly insufficient, return score 0 with an explanation that the resume could not be evaluated.`;

async function test(modelName) {
    console.log(`Testing model: ${modelName}`);
    try {
        const model = genAI.getGenerativeModel({
            model: modelName,
            systemInstruction: SYSTEM_PROMPT,
            generationConfig: {
                temperature: 0.1,
                maxOutputTokens: 400
            }
        });
        const result = await model.generateContent('JOB TITLE: Full Stack Developer\n\nJOB DESCRIPTION: Looking for Node and React\n\nRESUME: I am a node and react developer.');
        console.log(`✅ Success with ${modelName}:`, result.response.text());
    } catch (err) {
        console.log(`❌ Failed with ${modelName}:`, err.message);
    }
}

async function runAll() {
    await test('gemini-flash-latest');
    await test('gemini-2.5-flash-lite');
    await test('gemini-3.1-flash-lite');
}
runAll();
