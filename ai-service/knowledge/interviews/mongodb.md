# MongoDB Interview Guide

## Core Concepts
- **Document Model**: Understanding BSON, flexible schemas, and when to embed vs. reference data.
- **Aggregation Pipeline**: Can the candidate write complex `$match`, `$group`, and `$project` queries?
- **Indexes**: Understanding compound indexes, covered queries, and the `explain()` plan.

## Red Flags
- Treating MongoDB like a relational database (heavy reliance on application-side joins or `$lookup` for everything).
- Unbounded array growth in documents.
- Not understanding the implications of Write Concerns and Read Preferences in a Replica Set.
