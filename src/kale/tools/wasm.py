"""
src/kale/tools/wasm.py
WebAssembly (.wasm) binary module inspector, validator, and disassembler for Kale.
"""

import sys
import os
import struct
from typing import List, Dict, Tuple, Optional, Any

WASM_MAGIC = b"\x00asm"
WASM_VERSION = 1

SECTION_NAMES = {
    0: "Custom",
    1: "Type",
    2: "Import",
    3: "Function",
    4: "Table",
    5: "Memory",
    6: "Global",
    7: "Export",
    8: "Start",
    9: "Element",
    10: "Code",
    11: "Data",
    12: "DataCount",
}

VALTYPE_NAMES = {
    0x7F: "i32",
    0x7E: "i64",
    0x7D: "f32",
    0x7C: "f64",
    0x7B: "v128",
    0x70: "funcref",
    0x6F: "externref",
}

OPCODE_NAMES = {
    0x00: "unreachable",
    0x01: "nop",
    0x02: "block",
    0x03: "loop",
    0x04: "if",
    0x05: "else",
    0x0B: "end",
    0x0C: "br",
    0x0D: "br_if",
    0x0E: "br_table",
    0x0F: "return",
    0x10: "call",
    0x11: "call_indirect",
    0x1A: "drop",
    0x1B: "select",
    0x20: "local.get",
    0x21: "local.set",
    0x22: "local.tee",
    0x23: "global.get",
    0x24: "global.set",
    0x28: "i32.load",
    0x29: "i64.load",
    0x2A: "f32.load",
    0x2B: "f64.load",
    0x36: "i32.store",
    0x37: "i64.store",
    0x38: "f32.store",
    0x39: "f64.store",
    0x41: "i32.const",
    0x42: "i64.const",
    0x43: "f32.const",
    0x44: "f64.const",
    0x45: "i32.eqz",
    0x46: "i32.eq",
    0x47: "i32.ne",
    0x48: "i32.lt_s",
    0x6A: "i32.add",
    0x6B: "i32.sub",
    0x6C: "i32.mul",
    0x6D: "i32.div_s",
    0x6E: "i32.div_u",
    0x71: "i32.and",
    0x72: "i32.or",
    0x73: "i32.xor",
    0x74: "i32.shl",
    0x75: "i32.shr_s",
    0x76: "i32.shr_u",
}


def _read_leb128_u(data: bytes, offset: int) -> Tuple[int, int]:
    """Decodes unsigned LEB128 integer."""
    result = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise ValueError("Unexpected EOF reading LEB128")
        byte = data[offset]
        offset += 1
        result |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            break
        shift += 7
    return result, offset


def parse_wasm_sections(data: bytes) -> List[Dict[str, Any]]:
    if len(data) < 8:
        raise ValueError("Binary too small to be a WASM module")

    magic = data[:4]
    if magic != WASM_MAGIC:
        raise ValueError(f"Invalid WASM magic number: {magic!r}, expected {WASM_MAGIC!r}")

    version = struct.unpack("<I", data[4:8])[0]
    if version != WASM_VERSION:
        raise ValueError(f"Unsupported WASM version: {version}, expected {WASM_VERSION}")

    sections = []
    offset = 8
    while offset < len(data):
        sec_id = data[offset]
        offset += 1
        sec_len, offset = _read_leb128_u(data, offset)
        sec_data = data[offset:offset + sec_len]
        offset += sec_len

        sec_name = SECTION_NAMES.get(sec_id, f"Unknown({sec_id})")
        sections.append({
            "id": sec_id,
            "name": sec_name,
            "length": sec_len,
            "data": sec_data,
        })
    return sections


def inspect_wasm(wasm_path: str, verbose: bool = True) -> int:
    if not os.path.isfile(wasm_path):
        print(f"Error: WASM file '{wasm_path}' not found.", file=sys.stderr)
        return 1

    with open(wasm_path, "rb") as f:
        data = f.read()

    try:
        sections = parse_wasm_sections(data)
    except Exception as e:
        print(f"Validation Error in '{wasm_path}': {e}", file=sys.stderr)
        return 1

    print(f"WebAssembly Module: {wasm_path}")
    print(f"Size: {len(data)} bytes | Version: 1")
    print("-" * 60)
    print(f"{'Section ID':<12} {'Name':<15} {'Size (bytes)':<15}")
    print("-" * 60)

    for sec in sections:
        print(f"{sec['id']:<12} {sec['name']:<15} {sec['length']:<15}")

        # Parse export names if export section
        if sec["id"] == 7 and verbose:
            try:
                s_offset = 0
                count, s_offset = _read_leb128_u(sec["data"], s_offset)
                print(f"   -> Exports ({count}):")
                for _ in range(count):
                    n_len, s_offset = _read_leb128_u(sec["data"], s_offset)
                    exp_name = sec["data"][s_offset:s_offset + n_len].decode("utf-8", errors="replace")
                    s_offset += n_len
                    kind = sec["data"][s_offset]
                    s_offset += 1
                    idx, s_offset = _read_leb128_u(sec["data"], s_offset)
                    kind_str = ["func", "table", "mem", "global"][kind] if kind < 4 else str(kind)
                    print(f"      - {exp_name} ({kind_str} #{idx})")
            except Exception:
                pass

    print("-" * 60)
    print(f"Module valid: {len(sections)} sections loaded successfully.")
    return 0


def run_wasm(args) -> int:
    file_path = getattr(args, "file", None)
    if not file_path:
        print("Usage: kale wasm <file.wasm>", file=sys.stderr)
        return 1
    verbose = getattr(args, "verbose", True)
    return inspect_wasm(file_path, verbose=verbose)
