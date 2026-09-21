"""
tools/bindgen/bindgen.py
kale-bindgen — Automatic C Header to Kale FFI Binding Generator

Parses C header files (.h) and outputs clean, idiomatic Kale (.kl) code:
- C function prototypes -> `extern <type> <name>(<params>);`
- C structs -> `struct <Name> { <fields> }`
- C #define constants -> constant getter functions `fn int NAME() { return <val>; }`
- Primitive type mapping (int, char*, void*, float, double, uint32_t, size_t, etc.)
"""

import re
import sys
import os
import argparse
from typing import List, Tuple, Dict

TYPE_MAP = {
    "void": "void",
    "void*": "void*",
    "const void*": "void*",
    "char*": "string",
    "const char*": "string",
    "char": "char",
    "int": "int",
    "signed int": "int",
    "unsigned int": "int",
    "short": "int",
    "unsigned short": "int",
    "long": "int",
    "unsigned long": "int",
    "long long": "int",
    "unsigned long long": "int",
    "int8_t": "int",
    "uint8_t": "int",
    "int16_t": "int",
    "uint16_t": "int",
    "int32_t": "int",
    "uint32_t": "int",
    "int64_t": "int",
    "uint64_t": "int",
    "size_t": "int",
    "float": "float",
    "double": "double",
    "bool": "bool",
    "_Bool": "bool",
}

def map_c_type(c_type: str) -> str:
    c_type = c_type.strip()
    # Normalize pointers: "char *" -> "char*"
    c_type = re.sub(r'\s*\*\s*', '*', c_type)
    c_type = re.sub(r'\bconst\s+', '', c_type).strip()

    if c_type in TYPE_MAP:
        return TYPE_MAP[c_type]
    if c_type.endswith("*"):
        base = c_type[:-1].strip()
        if base in TYPE_MAP:
            mapped_base = TYPE_MAP[base]
            if mapped_base == "string":
                return "string"
            return f"{mapped_base}*"
        return f"{base}*"
    return c_type


class CBindingGenerator:
    def __init__(self, module_name: str = "bindings"):
        self.module_name = module_name
        self.constants: List[Tuple[str, str, str]] = []  # (name, val, type)
        self.structs: List[Tuple[str, List[Tuple[str, str]]]] = []  # (name, [(type, name)])
        self.functions: List[Tuple[str, str, List[Tuple[str, str]], bool]] = []  # (ret_type, name, [(type, name)], is_variadic)

    def parse_header(self, content: str):
        # Remove C/C++ comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        content = re.sub(r'//.*', '', content)

        # 1. Parse #define NUMERIC_CONST 123
        for match in re.finditer(r'#define\s+([A-Za-z_][A-Za-z0-9_]*)\s+([0-9xXxa-fA-F\.\-]+)\b', content):
            name = match.group(1)
            val = match.group(2)
            val_type = "float" if "." in val else "int"
            self.constants.append((name, val, val_type))

        # 2. Parse typedef struct or struct definitions
        struct_pattern = re.compile(r'(?:typedef\s+)?struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{([^}]+)\}(?:\s*([A-Za-z_][A-Za-z0-9_]*))?;', re.MULTILINE)
        for match in struct_pattern.finditer(content):
            tag_name = match.group(1)
            body = match.group(2)
            typedef_name = match.group(3)
            struct_name = typedef_name or tag_name
            fields = []
            for field_line in body.split(';'):
                field_line = field_line.strip()
                if not field_line:
                    continue
                # match type and name: int x or char* name
                f_match = re.match(r'(.+?)\s+([A-Za-z_][A-Za-z0-9_]*)$', field_line)
                if f_match:
                    f_type = map_c_type(f_match.group(1))
                    f_name = f_match.group(2)
                    fields.append((f_type, f_name))
            if fields:
                self.structs.append((struct_name, fields))

        # 3. Parse function declarations
        # e.g.: int foo(char* bar, void* baz);
        fn_pattern = re.compile(r'([A-Za-z0-9_\*\s]+?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*;', re.MULTILINE)
        for match in fn_pattern.finditer(content):
            ret_raw = match.group(1).strip()
            # Ignore preprocessor, typedef, or return statements
            if ret_raw.startswith("#") or "typedef" in ret_raw or "return" in ret_raw:
                continue
            ret_type = map_c_type(ret_raw)
            fn_name = match.group(2)
            params_raw = match.group(3).strip()

            params = []
            is_var = False
            if params_raw and params_raw != "void":
                for p in params_raw.split(','):
                    p = p.strip()
                    if p == "...":
                        is_var = True
                        continue
                    p_match = re.match(r'(.+?)(?:\s+([A-Za-z_][A-Za-z0-9_]*))?$', p)
                    if p_match:
                        p_type = map_c_type(p_match.group(1))
                        p_name = p_match.group(2) or f"arg{len(params)}"
                        params.append((p_type, p_name))

            self.functions.append((ret_type, fn_name, params, is_var))

    def generate_kale(self) -> str:
        lines = []
        lines.append(f"// Automatically generated by kale-bindgen")
        lines.append(f"// Module: {self.module_name}\n")

        # Constants
        if self.constants:
            lines.append("// ── Constants ──")
            for name, val, val_type in self.constants:
                lines.append(f"fn {val_type} {name}() {{ return {val}; }}")
            lines.append("")

        # Structs
        if self.structs:
            lines.append("// ── Structs ──")
            for sname, fields in self.structs:
                lines.append(f"struct {sname} {{")
                for ftype, fname in fields:
                    lines.append(f"    {ftype} {fname};")
                lines.append("}\n")

        # Functions
        if self.functions:
            lines.append("// ── External Functions ──")
            for ret, name, params, is_var in self.functions:
                param_strs = [f"{pt} {pn}" for pt, pn in params]
                if is_var:
                    param_strs.append("...")
                param_list = ", ".join(param_strs)
                lines.append(f"extern {ret} {name}({param_list});")
            lines.append("")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="kale-bindgen — C Header to Kale FFI Generator")
    parser.add_argument("header", help="Path to C header file (.h)")
    parser.add_argument("-o", "--out", help="Output path for .kl file", default=None)
    parser.add_argument("-m", "--module", help="Module name", default="bindings")

    args = parser.parse_args()

    if not os.path.isfile(args.header):
        print(f"Error: Header not found '{args.header}'", file=sys.stderr)
        sys.exit(1)

    with open(args.header, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    gen = CBindingGenerator(module_name=args.module)
    gen.parse_header(content)
    output = gen.generate_kale()

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Generated {len(gen.functions)} functions, {len(gen.structs)} structs, {len(gen.constants)} constants -> {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()
