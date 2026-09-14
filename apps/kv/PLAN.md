# apps/kv Architecture Plan

## 1. Overview
kaledis: High-performance, Redis-compatible in-memory key-value database engine and TCP network daemon for Kale.

## 2. Modules
- `store.kl`: In-memory hash map storage engine with full `strcmp` key matching, CRUD (SET, GET, DEL, EXISTS), capacity tracking, slot reuse, and key enumeration (`store_get_key_at`).
- `daemon.kl`: TCP network daemon powered by `libs/net/tcp.kl`. Provides Redis RESP Array protocol parser and inline command dispatcher (PING, ECHO, SET, GET, DEL, EXISTS, DBSIZE, KEYS, FLUSHDB, INFO, QUIT) with strict arity validation.
- `main.kl`: Server bootstrap and integration verification runner.

## 3. Wire Protocol
Supports standard line-based and RESP array wire protocols over raw TCP sockets:
- Arrays: `*<count>\r\n$<len>\r\n<data>\r\n...`
- Simple Strings: `+OK\r\n`, `+PONG\r\n`
- Bulk Strings: `$len\r\n<data>\r\n`, `$-1\r\n` (nil)
- Integers: `:<n>\r\n`
- Errors: `-ERR <reason>\r\n`
