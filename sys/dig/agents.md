# sys/dig — DNS Resolver & Diagnostic CLI

## Version
`0.1.0`

## Description
Low-level packet-crafted DNS query tool and resolver written in pure Kale. Delivers fast DNS inspection (A, AAAA, MX, TXT, CNAME, NS) directly over UDP/TCP sockets.

## Status
🟡 In Progress

## Dependencies
- `libs/net`: raw UDP/TCP sockets
- `packages/std`: byte buffers, collections

## Build Instructions
```bash
kale build sys/dig/main.kl -o bin/kale_dig.exe -lws2_32
./bin/kale_dig.exe google.com A
```
