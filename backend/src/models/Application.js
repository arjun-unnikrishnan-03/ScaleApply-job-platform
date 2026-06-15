const mongoose = require("mongoose");

const applicationSchema = new mongoose.Schema(
    {
        userId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true, index: true },
        jobId: { type: mongoose.Schema.Types.ObjectId, ref: "Job", required: true, index: true },
        resumeKey: { type: String, required: true },
        resumeOriginalName: { type: String },
        score: { type: Number, default: null }, // Legacy generic score
        explanation: { type: String, default: null }, // Legacy generic explanation
        scoredAt: { type: Date, default: null },
        
        // --- New AI Engine Fields ---
        atsResult: { type: mongoose.Schema.Types.Mixed, default: null },
        skillGapAnalysis: { type: mongoose.Schema.Types.Mixed, default: null },
        recruiterDecision: { type: mongoose.Schema.Types.Mixed, default: null },
    },
    { timestamps: true }
);

applicationSchema.index({ userId: 1, jobId: 1 }, { unique: true });
applicationSchema.index({ jobId: 1, score: -1 });

module.exports = mongoose.model("Application", applicationSchema);
