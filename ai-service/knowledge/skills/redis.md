# Redis Knowledge Base

Redis is an open source (BSD licensed), in-memory data structure store, used as a database, cache, and message broker.

## Data Types
- **Strings**: The most basic kind of Redis value.
- **Lists**: Lists of strings, sorted by insertion order.
- **Sets**: Unordered collections of unique strings.
- **Hashes**: Maps between string fields and string values.
- **Sorted Sets**: Similar to Sets but where every string element is associated with a floating number value, called score.

## Use Cases
- Session Cache
- Full Page Cache (FPC)
- Leaderboards/Counting
- Pub/Sub
- Queues
