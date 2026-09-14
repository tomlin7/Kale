# Web Framework (`libs/web`) Plan

## 1. Overview
`libs/web` is a modern, expressive web application framework written natively in Kale. It provides routing, request/response lifecycle abstractions, middleware chaining, and template rendering.

---

## 2. Directory Layout & Subsystems

```
libs/web/
├── router.kl        # Trie-based / parameter-matching URL router
├── request.kl       # Request context (params, query, body, headers)
├── response.kl      # Response builder (status, headers, JSON/HTML)
├── middleware.kl    # Middleware pipeline (logger, CORS, auth)
├── template.kl      # String interpolation template engine
└── PLAN.md
```

---

## 3. Implementation Status & Framework Features

### 3.1 Routing Engine (`router.kl`) - 🟢 Completed
- Dynamic parameter-matching router (`match_and_extract_params`).
- Matches both static paths (`/api/v1/health`) and dynamic segments (`/users/:id`, `/posts/:post_id/comments/:comment_id`).
- Supports `GET`, `POST`, `PUT`, `DELETE` methods with clean function pointer handlers `fn(Request*, Response*): void`.
- Automatic 404 fallback dispatch.

### 3.2 Request & Response Model (`request.kl` & `response.kl`) - 🟢 Completed
- `Request`: Parses method, path, URL query string (`/path?key=val`), headers, and raw payload.
- `ParamMap`: Lightweight key-value store for extracted dynamic params and query string values (`get_param`, `get_query`).
- `Response`: Ergonomic builders for `html()`, `json()`, `text()`, `status_code()`, and `not_found()`.
- Client response transmission via `send_to(client)`.

### 3.3 Templating Engine (`template.kl`) - 🟢 Completed
- Evaluates string templates replacing `{{ variable }}` placeholders with values from `TemplateContext`.
- Dynamic buffer scaling with zero memory corruption.

### 3.4 Web App Harness (`app.kl`) - 🟢 Completed
- Top-level `WebApp` coordinating `Router`, `HttpServer`, and `TcpStream` client dispatch loops.

---

## 4. Next Steps
- Middleware pipeline (`middleware.kl`) with chained next handlers.
- Static file serving from disk (`packages/std/fs`).
- Cookie and session state management.
