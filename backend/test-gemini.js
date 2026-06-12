require('dotenv').config();
const { scoreResume } = require('./src/services/aiService');

async function testGeminiIntegration() {
    console.log("Testing Gemini API Job Matching...\n");

    const mockJob = {
        title: "Full Stack Developer",
        description: "Looking for a full stack developer with experience in Node.js and React. Familiarity with AWS is a plus."
    };

    const mockResume = "Senior Software Engineer with 5 years of experience building web applications using Node.js, Express, and React. Deployed multiple services to AWS using Docker.";

    try {
        console.log("Evaluating Resume:");
        console.log(mockResume);
        console.log("\nAgainst Job Description:");
        console.log(mockJob.description);
        console.log("\nWaiting for Gemini to score...");
        
        const result = await scoreResume({
            resumeText: mockResume,
            jobTitle: mockJob.title,
            jobDescription: mockJob.description
        });

        console.log("\n✅ Result from Gemini:");
        console.log(`Score: ${result.score}/100`);
        console.log(`Explanation: ${result.explanation}`);
        
    } catch (error) {
        console.error("\n❌ Test failed:", error.message);
    }
}

testGeminiIntegration();
