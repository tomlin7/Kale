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

## 3. Architecture Details

### 3.1 Socket Layer (`socket.kl` & `tcp.kl`)
- Windows initialization: Calls `WSAStartup` automatically.
- Socket handles wrapped in `TcpStream` and `TcpListener`.
- Supports blocking and non-blocking modes (`ioctlsocket` / `fcntl`).

### 3.2 HTTP/1.1 Engine (`http.kl` & `server.kl`)
- **HTTP Client**:
  - `http_get(url: string) -> HttpResponse`
  - `http_post(url: string, body: string, content_type: string) -> HttpResponse`
  - Handles Chunked Transfer Encoding and Keep-Alive connection pools.
- **HTTP Server**:
  - Single-threaded event-driven accept loop.
  - Parses HTTP request lines, headers (`Host`, `User-Agent`, `Content-Length`), and payloads.
  - Formats valid HTTP/1.1 status responses (`200 OK`, `404 Not Found`, `500 Internal Server Error`).
