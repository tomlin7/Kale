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

## 3. Framework Features

### 3.1 Routing Engine (`router.kl`)
- Matches standard paths: `/api/v1/health`.
- Matches dynamic route segments: `/users/:user_id/posts/:post_id`.
- Fast lookups using string hash map or prefix trie.

### 3.2 Request & Response Model
```
struct Request {
    string method;
    string path;
    StringMap<string> params;
    StringMap<string> query;
    StringMap<string> headers;
    string body;
}

struct Response {
    int32 status;
    StringMap<string> headers;
    string body;

    fn void json(data: string)
    fn void html(content: string)
    fn void redirect(url: string)
}
```

### 3.3 Templating (`template.kl`)
- Evaluates string templates with variable replacement (`{{ title }}`).
- Conditional blocks (`{% if is_logged_in %}`).
- Loop blocks (`{% for item in items %}`).
