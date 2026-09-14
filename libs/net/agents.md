# Networking Library

## Version
`0.1.0`

## Description
Networking library providing TCP/UDP sockets via Winsock2 (ws2_32.dll) and a zero-dependency HTTP/1.1 client and single-threaded HTTP server in pure Kale.

## Status
Current status: 🟢 Active (Milestone Completed)

## Dependencies
- PythonKale compiler
- packages/std
- Winsock2 (ws2_32.dll)

## Build Instructions
Link with `-lws2_32` (e.g. `kale build examples/net_smoke.kl -o bin/net_smoke.exe -lws2_32`)

## Coding Conventions
- PascalCase for structs (SockAddrIn, TcpStream, TcpListener, HttpRequest, HttpResponse, HttpServer), snake_case for functions
- Clean separation between low-level socket FFI (`libs/net/socket.kl`) and high-level stream/protocol abstractions (`libs/net/tcp.kl`, `libs/net/http.kl`, `libs/net/server.kl`)

## Short-term Milestones
- [x] Winsock2 initialization and raw socket FFI
- [x] `TcpStream` and `TcpListener` stream wrappers
- [x] HTTP/1.1 client (`http_get`, `http_post`, URL parsing)
- [x] HTTP/1.1 server (`http_listen`, request parsing, response generation)
- [ ] Non-blocking async I/O / multiplexing with `select()`
- [ ] TLS / HTTPS support via Schannel / OpenSSL
- [ ] WebSocket RFC 6455 frame protocol

## Future Plans
High-concurrency async event loop, connection pooling, HTTP/2 protocol support.
