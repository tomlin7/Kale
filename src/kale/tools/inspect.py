"""Deep symbol table and memory layout inspector for Kale structs and types."""

from __future__ import annotations

import re
import sys
from pathlib import Path


TYPE_SIZES = {
    "int": 4,
    "int32": 4,
    "int64": 8,
    "float": 4,
    "double": 8,
    "char": 1,
    "bool": 1,
    "string": 8,
    "void*": 8,
}


def inspect_source(file_path: str) -> int:
    p = Path(file_path)
    if not p.exists():
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        return 1

    content = p.read_text(encoding="utf-8")
    print(f"\033[1;34m[kale inspect]\033[0m Analyzing memory layout and symbols in '{p.name}'...\n")

    # Match structs
    struct_pattern = re.compile(r"struct\s+([A-Za-z0-9_]+)\s*\{([^}]*)\}")
    matches = struct_pattern.findall(content)

    if not matches:
        print("No struct definitions found.")
        return 0

    for s_name, s_body in matches:
        print("=" * 64)
        print(f" STRUCT: {s_name}")
        print("=" * 64)
        print(f"{'OFFSET':<10} {'FIELD':<22} {'TYPE':<16} {'SIZE':<8}")
        print("-" * 64)

        cur_offset = 0
        fields = [f.strip() for f in s_body.split(";") if f.strip()]

        for f in fields:
            parts = f.split()
            if len(parts) >= 2:
                f_type = parts[0]
                f_name = parts[1]

                # Determine size
                f_size = 8 if "*" in f_type else TYPE_SIZES.get(f_type, 8)

                # Alignment padding (align to min(f_size, 8))
                align = min(f_size, 8)
                if align > 0 and (cur_offset % align) != 0:
                    pad = align - (cur_offset % align)
                    print(f"+{cur_offset:<9} {'<padding>':<22} {'byte':<16} {pad:<8}")
                    cur_offset += pad

                print(f"+{cur_offset:<9} {f_name:<22} {f_type:<16} {f_size:<8}")
                cur_offset += f_size

        # Struct tail alignment
        tail_pad = (8 - (cur_offset % 8)) % 8
        if tail_pad > 0:
            print(f"+{cur_offset:<9} {'<tail padding>':<22} {'byte':<16} {tail_pad:<8}")
            cur_offset += tail_pad

        print("-" * 64)
        print(f"Total Size: {cur_offset} bytes | Alignment: 8 bytes\n")

    return 0
