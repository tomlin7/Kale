# Web Framework

## Version
`0.0.1`

## Description
Web application framework written in Kale. Provides URL routing, request/response handling, and a simple template engine.

## Status
Current status: 🔴 Not Started

## Dependencies
- libs/net
- packages/std

## Build Instructions
Imported by web apps via `import "libs/web/..." as alias;`

## Coding Conventions
- PascalCase for framework structs (Router, Context, Template), snake_case for handler and helper functions
- Idiomatic request/response pipelines and composable handlers

## Short-term Milestones
- [ ] Router
- [ ] Request/response types
- [ ] Template engine with variable interpolation

## Future Plans
Middleware, session management, static file serving, WebSocket support.
