const mongoose = require("mongoose");

const userSchema = new mongoose.Schema({
    email: { type: String, required: true, unique: true },
    password: { type: String, required: true },
    role: {
        type: String,
        enum: ["recruiter", "candidate"],
        required: true
    },
    candidateProfile: {
        type: mongoose.Schema.Types.Mixed,
        default: null
    }
}, { timestamps: true });

module.exports = mongoose.model("User", userSchema);