require('dotenv').config();
const { analyzeResume, evaluateATS, queryKnowledgeBase } = require('./src/services/aiClient');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function testAIIntegration() {
    console.log("==================================================");
    console.log("  Testing AI BFF Integration (Node.js -> FastAPI) ");
    console.log(`  Targeting AI Service: ${process.env.AI_SERVICE_URL || 'http://localhost:8000'}`);
    console.log("==================================================\n");

    const mockResumeText = `
    Arjun Unnikrishnan
    Software Engineer
    Email: arjun@example.com
    Experience:
    - Senior Full Stack Developer at Tech Corp (2022 - Present)
      Built web applications using Node.js, Express, and React. Deployed multiple services to AWS.
    Skills: Node.js, React, JavaScript, AWS, MongoDB, Docker
    `;

    const mockJob = {
        title: "Full Stack Developer",
        company_name: "Innovate Inc",
        summary: "We are looking for a Software Engineer experienced with React and Node.js backend databases. Knowledge of AWS is a plus.",
        required_skills: ["React", "Node.js", "MongoDB", "AWS"],
        preferred_skills: [],
        technologies: [],
        responsibilities: [],
        qualifications: []
    };

    try {
        console.log("1. Testing analyzeResume...");
        console.log("Sending mock resume text to AI service for parsing...");
        const parsedProfile = await analyzeResume(mockResumeText);
        console.log("✅ Success! Parsed candidate profile response:");
        console.log(JSON.stringify(parsedProfile, null, 2));

        console.log("\nWaiting 4 seconds to cool down rate limits...");
        await sleep(4000);

        console.log("\n2. Testing evaluateATS...");
        console.log("Sending parsed candidate profile and job description to AI service for evaluation...");
        const evaluationResult = await evaluateATS(parsedProfile, mockJob);
        console.log("✅ Success! ATS Evaluation response:");
        console.log(JSON.stringify(evaluationResult, null, 2));

        console.log("\nWaiting 4 seconds to cool down rate limits...");
        await sleep(4000);

        console.log("\n3. Testing queryKnowledgeBase (RAG)...");
        console.log("Sending RAG query to AI service...");
        const queryResult = await queryKnowledgeBase("What are the key responsibilities of a backend engineer?", 2);
        console.log("✅ Success! RAG query response:");
        console.log(JSON.stringify(queryResult, null, 2));

        console.log("\n🎉 ALL BFF END-TO-END TESTS PASSED SUCCESSFULLY! 🎉");
    } catch (error) {
        console.error("\n❌ Test failed:", error.message);
        process.exit(1);
    }
}

testAIIntegration();
