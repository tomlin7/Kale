# Database Driver

## Version
`0.0.1`

## Description
SQLite3 database bindings and query builder for Kale.

## Status
Current status: 🔴 Not Started

## Dependencies
- PythonKale compiler
- sqlite3.dll

## Build Instructions
Link with sqlite3 library

## Coding Conventions
- PascalCase for structs (Connection, Statement, Row), snake_case for functions
- Safe wrappers around raw C SQLite pointers with resource lifecycle cleanup

## Short-term Milestones
- [ ] SQLite3 extern bindings
- [ ] DB open/close/exec
- [ ] Prepared statements
- [ ] Query result iteration

## Future Plans
PostgreSQL driver, connection pooling, ORM layer.
