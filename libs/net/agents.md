# Networking Library

## Version
`0.0.1`

## Description
Networking library providing TCP/UDP sockets via Winsock2 and a minimal HTTP/1.1 client and server.

## Status
Current status: 🔴 Not Started

## Dependencies
- PythonKale compiler
- packages/std
- Winsock2 (ws2_32.dll)

## Build Instructions
Link with `-lws2_32`

## Coding Conventions
- PascalCase for structs (Socket, HttpRequest, HttpResponse), snake_case for functions
- Clean separation between low-level socket FFI and high-level protocol abstractions

## Short-term Milestones
- [ ] Raw TCP sockets
- [ ] HTTP GET/POST client
- [ ] Basic HTTP server with routing

## Future Plans
TLS support, WebSocket, async I/O.
