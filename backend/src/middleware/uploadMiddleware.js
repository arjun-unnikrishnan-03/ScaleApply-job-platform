const multer = require("multer");
const multerS3 = require("multer-s3");
const path = require("path");
const crypto = require("crypto");
const s3 = require("../config/s3");
const env = require("../config/env");

const ALLOWED_MIME = new Set([
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]);
const ALLOWED_EXT = new Set([".pdf", ".doc", ".docx"]);

const fileFilter = (_req, file, cb) => {
    const ext = path.extname(file.originalname || "").toLowerCase();
    if (ALLOWED_MIME.has(file.mimetype) && ALLOWED_EXT.has(ext)) return cb(null, true);
    cb(new Error("Error: Only PDF, DOC, and DOCX files are allowed"));
};

const upload = multer({
    storage: multerS3({
        s3,
        bucket: env.aws.bucket,
        contentType: multerS3.AUTO_CONTENT_TYPE,
        key: (req, file, cb) => {
            const ext = path.extname(file.originalname || "").toLowerCase();
            const uid = req.user?._id || "anon";
            const rand = crypto.randomBytes(8).toString("hex");
            cb(null, `resumes/${uid}/${Date.now()}-${rand}${ext}`);
        }
    }),
    limits: { fileSize: 5 * 1024 * 1024 },
    fileFilter
});

module.exports = upload;
