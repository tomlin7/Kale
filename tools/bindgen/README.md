# tools/bindgen — kale-bindgen

Automatic C Header to Kale FFI Binding Generator.

## Usage

```bash
python tools/bindgen/bindgen.py <header.h> -o <output.kl> -m <module_name>
```

## Features

- **Constants**: Translates `#define CONST 123` into `fn int CONST() { return 123; }`.
- **Structs**: Translates C `struct` / `typedef struct` declarations into Kale `struct Name { ... }`.
- **Functions**: Translates C function prototypes into `extern <type> <name>(<params>);`.
- **Type Mapping**: Automatically converts `char*` / `const char*` to `string`, `void*` to `void*`, `int32_t`/`size_t` to `int`, etc.
