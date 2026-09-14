# apps/kv Architecture Plan

## 1. Overview
kaledis: High-performance, Redis-compatible in-memory key-value database engine and TCP network daemon for Kale.

## 2. Modules
- `store.kl`: In-memory hash map storage engine with full `strcmp` key matching, CRUD (SET, GET, DEL, EXISTS), capacity tracking, and slot reuse.
- `daemon.kl`: TCP network daemon powered by `libs/net/tcp.kl`. Provides Redis RESP protocol command parsing (PING, SET, GET, DEL, EXISTS, DBSIZE, FLUSHDB, INFO, QUIT) and client request-response dispatch.
- `main.kl`: Server bootstrap and integration verification runner.

## 3. Wire Protocol
Supports standard line-based and RESP wire protocols over raw TCP sockets:
- Simple Strings: `+OK\r\n`, `+PONG\r\n`
- Bulk Strings: `$len\r\n<data>\r\n`, `$-1\r\n` (nil)
- Integers: `:<n>\r\n`
- Errors: `-ERR <reason>\r\n`
