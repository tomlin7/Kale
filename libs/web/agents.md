# Web Framework

## Version
`0.1.0`

## Description
Web application framework written natively in Kale. Provides parameter-matching URL routing, HTTP request/response abstractions, and a string-interpolating template engine.

## Status
Current status: 🟢 Active (Milestone Completed)

## Dependencies
- libs/net
- packages/std

## Build Instructions
Imported by web apps via `import "libs/web/..." as alias;`
Link with `-lws2_32` (e.g. `kale build examples/web_smoke.kl -o bin/web_smoke.exe -lws2_32`)

## Coding Conventions
- PascalCase for framework structs (`Router`, `Request`, `Response`, `TemplateContext`, `Template`, `WebApp`), snake_case for handler and helper functions
- Idiomatic request/response pipelines and composable handlers

## Short-term Milestones
- [x] Parameter-matching URL router (`:param` dynamic segments and static paths)
- [x] Request and response types (`Request.get_param`, `Request.get_query`, `Response.html`, `Response.json`, `Response.text`)
- [x] String-interpolating template engine (`{{ variable }}` placeholder replacement)
- [x] Top-level web application harness (`WebApp`)
- [ ] Middleware chaining pipeline (logging, CORS, authentication)
- [ ] Static file serving from disk
- [ ] Cookie and session management

## Future Plans
WebSocket RFC 6455 support, multipart form body parser, template loops/conditionals.
