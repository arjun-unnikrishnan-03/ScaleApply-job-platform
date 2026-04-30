const mongoose = require("mongoose");

const applicationSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },
    jobId: { type: mongoose.Schema.Types.ObjectId, ref: "Job", required: true },
    resumeUrl: { type: String, required: true },
    score: Number,
    explanation: String
}, { timestamps: true });

module.exports = mongoose.model("Application", applicationSchema);