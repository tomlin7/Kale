# Database Driver (`libs/sql`)

## Version
`0.1.0`

## Description
SQLite3 database bindings, connection abstraction, prepared statements, row iteration, and type-safe query builder for Kale.

## Status
Current status: 🟢 Active (Stable v0.1.0)

## Dependencies
- PythonKale compiler (`src/kale`)
- SQLite3 64-bit DLL (`libs/sql/bin/sqlite3.dll` or system `sqlite3.dll`)
- SQLite3 import library (`libs/sql/lib/sqlite3.lib`)

## Build Instructions
Link against the SQLite3 import library:
```powershell
uv run kale build <source.kl> -o <binary.exe> -LE:\kale\libs\sql\lib -lsqlite3
```

## Architecture & Modules
- `sqlite.kl`: Core FFI extern declarations for SQLite3 C API and status constants.
- `connection.kl`: `Database` struct providing safe lifecycle management, execution (`exec`), statement preparation, error introspection, and transaction management.
- `statement.kl`: `Statement` struct providing prepared statement binding (`bind_int`, `bind_double`, `bind_string`, `bind_null`), stepping (`step`), execution, and column extraction (`get_int`, `get_double`, `get_string`).
- `query_builder.kl`: Type-safe SQL query builder `QueryBuilder` with chaining support for `SELECT`, `WHERE` (AND-separated clauses), `ORDER BY`, `LIMIT`, and SQL statement generation.

## Completed Milestones
- [x] Vendored SQLite3 x64 DLL and generated Windows import library (`sqlite3.lib`)
- [x] Parser support for double pointer tokens (`void**`)
- [x] SQLite3 extern bindings (`libs/sql/sqlite.kl`)
- [x] Safe database open/close/exec wrappers with initialization lifecycle (`libs/sql/connection.kl`)
- [x] Prepared statements and parameter binding (`libs/sql/statement.kl`)
- [x] Query result iteration and typed column readers (`libs/sql/statement.kl`)
- [x] Fluent SQL Query Builder (`libs/sql/query_builder.kl`)
- [x] Comprehensive automated smoke test suite (`examples/sql_smoke.kl`)

## Future Plans
- SQLite transactions (`BEGIN TRANSACTION`, `COMMIT`, `ROLLBACK`) helper methods
- Connection pooling for multi-threaded/concurrent workers
- PostgreSQL and MySQL drivers
- Lightweight ORM schema mapping layer
