# Networking & Sockets Library (`libs/net`) Plan

## 1. Overview
`libs/net` provides zero-overhead cross-platform networking primitives, from raw TCP/UDP stream sockets to high-level HTTP/1.1 client and server implementations.

---

## 2. Directory Layout & Module Breakdown

```
libs/net/
├── socket.kl        # Winsock2 (ws2_32) & POSIX socket bindings
├── tcp.kl           # TcpStream and TcpListener abstractions
├── http.kl          # HttpClient: GET, POST, headers, body streaming
├── server.kl        # HttpServer: Request parsing, response writing
└── PLAN.md
```

---

## 3. Implementation Status & Architecture Details

### 3.1 Socket Layer (`socket.kl` & `tcp.kl`) - 🟢 Completed
- Windows initialization: Calls `WSAStartup(0x0202)` automatically on first use.
- Socket handles wrapped in `TcpStream` and `TcpListener`.
- Supports raw byte sending/receiving, string transmission, SO_REUSEADDR, and graceful shutdown.
- Tested and verified in `examples/net_smoke.kl`.

### 3.2 HTTP/1.1 Engine (`http.kl` & `server.kl`) - 🟢 Completed
- **HTTP Client**:
  - `http_get(url: string) -> HttpResponse`
  - `http_post(url: string, body: string, content_type: string) -> HttpResponse`
  - URL parser extracting host, explicit/implicit port, and request path.
  - Automatic status line extraction (e.g. 200, 404) and HTTP body separation.
- **HTTP Server**:
  - Single-threaded event accept loop via `tcp_listen`.
  - Parses HTTP request lines, paths, methods (`GET`, `POST`), and request bodies.
  - Generates valid RFC-compliant HTTP/1.1 status responses (`send_http_response`).
  - Tested and verified in `examples/net_smoke.kl`.

---

## 4. Next Steps
- Non-blocking socket polling via `select()`.
- Connection keep-alive and chunked transfer decoding.
- TLS support for HTTPS.
