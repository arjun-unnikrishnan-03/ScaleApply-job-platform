const { GetObjectCommand } = require("@aws-sdk/client-s3");
const s3 = require("../config/s3");

// Helper to extract the exact S3 object key from the public URL
const extractS3Key = (url) => {
    // Expected format: https://bucket-name.s3.region.amazonaws.com/12345-resume.pdf
    const urlParts = url.split(".amazonaws.com/");
    if (urlParts.length === 2) {
        // Decode URI component in case there are spaces or special characters in the filename
        return decodeURIComponent(urlParts[1]); 
    }
    return null;
};

// AWS SDK v3 returns a readable stream, we must convert it to a buffer
const streamToBuffer = async (stream) => {
    return new Promise((resolve, reject) => {
        const chunks = [];
        stream.on("data", (chunk) => chunks.push(chunk));
        stream.on("error", reject);
        stream.on("end", () => resolve(Buffer.concat(chunks)));
    });
};

const getFileBufferFromS3 = async (fileUrl) => {
    const key = extractS3Key(fileUrl);
    if (!key) throw new Error("Could not extract S3 key from URL");

    const command = new GetObjectCommand({
        Bucket: process.env.AWS_BUCKET_NAME,
        Key: key
    });

    const response = await s3.send(command);
    return await streamToBuffer(response.Body);
};

module.exports = { getFileBufferFromS3 };
