const { z } = require("zod");

const createJobSchema = z.object({
    title: z.string().trim().min(2).max(200),
    description: z.string().trim().min(10).max(10000)
});

const listJobsQuerySchema = z.object({
    search: z.string().trim().max(200).optional(),
    page: z.coerce.number().int().min(1).max(10000).default(1),
    limit: z.coerce.number().int().min(1).max(50).default(9)
});

const jobIdParamSchema = z.object({
    jobId: z.string().regex(/^[0-9a-fA-F]{24}$/, "Invalid id")
});

module.exports = { createJobSchema, listJobsQuerySchema, jobIdParamSchema };
