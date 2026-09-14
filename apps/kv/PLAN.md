# apps/kv Architecture Plan

## 1. Overview
A Redis-compatible in-memory key-value database demonstrating Kale's high-concurrency network capabilities.

## 2. Modules
- `resp.kl`: Redis Serialization Protocol parser and serializer.
- `skiplist.kl`: Probabilistic multi-level skip list for sorted sets and fast lookups.
- `storage.kl`: In-memory dictionary with TTL eviction and AOF snapshotting.
- `main.kl`: Asynchronous socket accept loop handling concurrent clients.
