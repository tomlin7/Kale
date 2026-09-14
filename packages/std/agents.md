# Standard Library

## Version
`0.2.0`

## Description
The official Kale standard library. Provides core types, collections, file I/O, filesystem, text processing, and system utilities. Includes modules for core/math, core/string, core/option, collections/list, collections/generic_list, collections/buffer, collections/map, fs/path, fs/dir, fs/file_util, io/file, sys/process, text/string_builder, and text/piece_table.

## Status
Current status: 🟡 In Progress

## Dependencies
- PythonKale compiler
- C runtime (msvcrt)

## Build Instructions
Imported by Kale programs via `import "packages/std/..." as alias;`

## Coding Conventions
- All modules are `.kl` files
- Use snake_case for functions, PascalCase for structs
- Each module should be self-contained

## Short-term Milestones
- [ ] Add iterators
- [ ] Add Result-based error handling patterns
- [ ] Add formatting/sprintf
- [ ] Add basic regex

## Future Plans
Complete standard library matching Rust/Go stdlib coverage.
