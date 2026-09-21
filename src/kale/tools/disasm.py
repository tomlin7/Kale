"""
src/kale/tools/disasm.py
Native binary and LLVM bitcode disassembler for Kale.
"""

import sys
import os
import shutil
import subprocess
from typing import Optional


def _find_disassembler() -> Optional[str]:
    # Check llvm-objdump
    p = shutil.which("llvm-objdump")
    if p:
        return p
    vs_llvm = r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\Llvm\bin\llvm-objdump.exe"
    if os.path.isfile(vs_llvm):
        return vs_llvm
    # Check dumpbin
    dumpbin = shutil.which("dumpbin")
    if dumpbin:
        return dumpbin
    return None


def disassemble_file(file_path: str, symbol: Optional[str] = None) -> int:
    if not os.path.isfile(file_path):
        print(f"Error: Target file '{file_path}' not found.", file=sys.stderr)
        return 1

    tool = _find_disassembler()
    if not tool:
        print("Error: llvm-objdump or dumpbin not found in PATH or Visual Studio installation.", file=sys.stderr)
        return 1

    is_llvm = "llvm-objdump" in tool.lower()
    cmd = [tool]

    if is_llvm:
        cmd.extend(["-d", "--no-show-raw-insn"])
        if symbol:
            cmd.extend([f"--disassemble-symbols={symbol}"])
    else:
        cmd.extend(["/DISASM"])

    cmd.append(file_path)

    print(f"Disassembling {file_path} using {os.path.basename(tool)}...")
    print("-" * 70)
    try:
        res = subprocess.run(cmd, text=True, capture_output=True)
        if res.returncode != 0:
            print(f"Disassembly failed:\n{res.stderr}", file=sys.stderr)
            return res.returncode
        lines = res.stdout.splitlines()
        # Limit initial output to 120 lines if very large
        max_lines = 150
        for i, line in enumerate(lines):
            if i >= max_lines:
                print(f"\n... [{len(lines) - max_lines} more lines truncated. Use redirect to save full output] ...")
                break
            print(line)
        print("-" * 70)
        return 0
    except Exception as e:
        print(f"Error executing disassembler: {e}", file=sys.stderr)
        return 1


def run_disasm(args) -> int:
    file_path = getattr(args, "file", None)
    if not file_path:
        print("Usage: kale disasm <executable_or_object_file> [--symbol <name>]", file=sys.stderr)
        return 1
    symbol = getattr(args, "symbol", None)
    return disassemble_file(file_path, symbol=symbol)
