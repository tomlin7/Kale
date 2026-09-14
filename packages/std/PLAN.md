# Kale Standard Library (`packages/std`) Architecture & Expansion Plan

## 1. Overview
The Kale Standard Library (`packages/std`) provides zero-dependency runtime utilities for data structures, filesystem inspection, text processing, and system operations.

---

## 2. Directory Layout & Module Specifications

```
packages/std/
├── core/
│   ├── math.kl           # abs, min, max, clamp, pow, sqrt
│   ├── string.kl         # strlen, strcmp, substr, indexOf, split
│   └── option.kl         # Option<T> and Result<T, E> monads
├── collections/
│   ├── list.kl           # IntList (heap array)
│   ├── generic_list.kl   # List<T> with push, pop, get, set, clear
│   ├── buffer.kl         # ByteBuffer with dynamic resizing
│   └── map.kl            # StringMap<V> (FNV-1a) & IntMap<V>
├── fs/
│   ├── path.kl           # join, dirname, basename, ext, is_absolute
│   ├── dir.kl            # Directory traversal (List<string>)
│   └── file_util.kl      # read_to_string, write_string, exists
├── io/
│   └── file.kl           # fopen, fclose, fputs, fgets, fflush wrappers
├── text/
│   ├── string_builder.kl # High-performance string concatenation
│   └── piece_table.kl    # Piece Table text buffer for editor
└── sys/
    └── process.kl        # exit, getenv, system
```

---

## 3. Planned Expansions

### 3.1 Advanced String Formatting (`std/text/format.kl`)
- Implement `sprintf`-style formatting or type-safe string interpolation helpers.

### 3.2 Enhanced Iterators (`std/collections/iterator.kl`)
- Define standard iterator contract for collections (`has_next() -> bool`, `next() -> T`).

### 3.3 Dynamic Memory Allocator Utilities (`std/core/mem.kl`)
- Arena allocator and pool allocator implementations for game loops and per-frame UI allocations.

---

## 4. Verification & Testing
- Unit tests in `tests/test_std_fs.py`, `tests/test_std_text.py`, `tests/test_collections.py`.
