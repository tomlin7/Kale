# apps/kv — High-Performance Key-Value Store & Network Daemon (kaledis)

## Version
`0.2.0`

## Description
In-memory, RESP-compatible key-value database and TCP network daemon written in pure Kale. Features string matching, CRUD operations, bulk/inline protocol parsing, and high-throughput socket request dispatch.

## Status
🟢 Active (Network Daemon Completed)

## Dependencies
- `libs/net`: TCP socket server and listener
- `packages/std`: collections, string builder

## Verification
- Unit & Network Tests: `kale run tests/test_kv_daemon.kl`
- Main Runner: `kale run apps/kv/main.kl`
