const axios = require("axios");

// Function to call Azure OpenAI to score the resume against the job description
const scoreResume = async (resumeText, jobDescription) => {
    try {
        const endpoint = process.env.AZURE_OPENAI_ENDPOINT;
        const key = process.env.AZURE_OPENAI_KEY;

        if (!endpoint || !key || key === "your_key") {
            console.warn("Azure OpenAI credentials not configured. Skipping AI scoring.");
            return { score: null, explanation: "AI credentials not configured" };
        }

        const prompt = `Score how well this resume matches the job from 0 to 100. Also give a short explanation. 
Please return ONLY a valid JSON object in this format: {"score": <number>, "explanation": "<string>"}

Resume: ${resumeText}

Job: ${jobDescription}`;

        const response = await axios.post(
            endpoint,
            {
                messages: [{ role: "user", content: prompt }],
                temperature: 0.2,
                max_tokens: 150
            },
            {
                headers: {
                    "Content-Type": "application/json",
                    "api-key": key
                }
            }
        );

        const content = response.data.choices[0].message.content;
        
        // Clean up markdown block if present and parse JSON
        const jsonString = content.replace(/```json|```/g, "").trim();
        const parsed = JSON.parse(jsonString);
        
        return { 
            score: parsed.score, 
            explanation: parsed.explanation 
        };
    } catch (error) {
        console.error("AI Scoring Error:", error.response?.data || error.message);
        return { score: null, explanation: "AI scoring failed" };
    }
};

module.exports = { scoreResume };
