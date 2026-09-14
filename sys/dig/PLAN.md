# sys/dig Architecture Plan

## 1. Overview
A standalone DNS resolution engine and command-line diagnostic tool.

## 2. Wire Protocol Architecture
- `packet.kl`: 12-byte DNS header builder, query section compression, RR parser.
- `record.kl`: Typed records (A, AAAA, MX, CNAME, TXT, SOA).
- `resolver.kl`: UDP query sender with timeout, retry, and TCP fallback.
- `main.kl`: CLI parsing, formatted output tables, latency measurement.
