const { GetObjectCommand } = require("@aws-sdk/client-s3");
const { getSignedUrl } = require("@aws-sdk/s3-request-presigner");
const s3 = require("../config/s3");
const env = require("../config/env");

const extractKey = (url) => {
    if (!url) return null;
    try {
        const u = new URL(url);
        return decodeURIComponent(u.pathname.replace(/^\//, ""));
    } catch {
        return null;
    }
};

const streamToBuffer = (stream) =>
    new Promise((resolve, reject) => {
        const chunks = [];
        stream.on("data", (chunk) => chunks.push(chunk));
        stream.on("error", reject);
        stream.on("end", () => resolve(Buffer.concat(chunks)));
    });

const getFileBuffer = async (urlOrKey) => {
    const key = urlOrKey.includes("://") ? extractKey(urlOrKey) : urlOrKey;
    if (!key) throw new Error("Invalid S3 reference");
    const response = await s3.send(new GetObjectCommand({ Bucket: env.aws.bucket, Key: key }));
    return streamToBuffer(response.Body);
};

const getSignedDownloadUrl = async (urlOrKey, expiresInSeconds = 300) => {
    const key = urlOrKey.includes("://") ? extractKey(urlOrKey) : urlOrKey;
    if (!key) throw new Error("Invalid S3 reference");
    const command = new GetObjectCommand({ Bucket: env.aws.bucket, Key: key });
    return getSignedUrl(s3, command, { expiresIn: expiresInSeconds });
};

module.exports = { getFileBuffer, getSignedDownloadUrl, extractKey };
