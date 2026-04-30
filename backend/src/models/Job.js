const mongoose = require("mongoose");

const jobSchema = new mongoose.Schema(
    {
        title: { type: String, required: true, trim: true },
        description: { type: String, required: true },
        recruiterId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true, index: true }
    },
    { timestamps: true }
);

jobSchema.index({ title: "text", description: "text" });
jobSchema.index({ createdAt: -1 });

module.exports = mongoose.model("Job", jobSchema);
