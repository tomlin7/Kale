# Relational Database Driver (`libs/sql`) Plan

## 1. Overview
`libs/sql` provides native database access for Kale applications, wrapping the SQLite3 C library and offering a type-safe query builder and record iterator.

---

## 2. Directory Layout & Module Specifications

```
libs/sql/
├── sqlite.kl        # Direct FFI bindings for sqlite3.dll
├── connection.kl    # Database connection handle & transaction manager
├── statement.kl     # Prepared statement lifecycle & parameter binding
├── result.kl        # QueryResult set and Row column extractors
├── query_builder.kl # Type-safe SQL statement generator
└── PLAN.md
```

---

## 3. SQLite3 C Binding Interface
- `sqlite3_open(filename: string, db: void**) -> int32`
- `sqlite3_close(db: void*) -> int32`
- `sqlite3_prepare_v2(db: void*, sql: string, nbyte: int32, stmt: void**, tail: string*) -> int32`
- `sqlite3_step(stmt: void*) -> int32`
- `sqlite3_finalize(stmt: void*) -> int32`
- `sqlite3_column_text(stmt: void*, col: int32) -> string`
- `sqlite3_column_int(stmt: void*, col: int32) -> int32`
- `sqlite3_column_double(stmt: void*, col: int32) -> float64`

---

## 4. Ergonomic Kale Interface
```
let db = Database::open("app.db");
db.exec("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT);");

let stmt = db.prepare("INSERT INTO users (name) VALUES (?);");
stmt.bind_string(1, "Alice");
stmt.execute();

let rows = db.query("SELECT id, name FROM users;");
while (rows.next()) {
    let id = rows.get_int(0);
    let name = rows.get_string(1);
}
```
