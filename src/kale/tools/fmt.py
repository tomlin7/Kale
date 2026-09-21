"""
src/kale/tools/fmt.py
Source code formatter for Kale (.kl).
Normalizes indentation (4 spaces), brace placement, operator padding, and blank lines.
"""

import os
import re
import sys
from typing import List, Tuple

def format_kale_source(code: str) -> str:
    lines = code.splitlines()
    formatted_lines: List[str] = []
    indent_level = 0
    in_multiline_comment = False
    prev_blank = False

    for raw_line in lines:
        stripped = raw_line.strip()

        # Handle empty line
        if not stripped:
            if not prev_blank and formatted_lines:
                formatted_lines.append("")
                prev_blank = True
            continue
        prev_blank = False

        # Multi-line comment tracking
        if in_multiline_comment:
            formatted_lines.append("    " * indent_level + stripped)
            if "*/" in stripped:
                in_multiline_comment = False
            continue

        if stripped.startswith("/*"):
            if "*/" not in stripped:
                in_multiline_comment = True
            formatted_lines.append("    " * indent_level + stripped)
            continue

        # Single-line comment: keep existing indentation
        if stripped.startswith("//"):
            formatted_lines.append("    " * indent_level + stripped)
            continue

        # Count closing braces at line start to dedent before printing
        leading_close = 0
        idx = 0
        while idx < len(stripped) and stripped[idx] == '}':
            leading_close += 1
            idx += 1
            while idx < len(stripped) and stripped[idx].isspace():
                idx += 1

        cur_indent = max(0, indent_level - leading_close)

        # Clean line content
        line = stripped

        # Normalize operator spacing if not in string
        # Space after commas
        line = re.sub(r',([^\s])', r', \1', line)
        # Space before opening brace
        line = re.sub(r'([^\s])\{', r'\1 {', line)
        # Clean double spaces
        line = re.sub(r'[ \t]+', ' ', line)

        formatted_lines.append("    " * cur_indent + line)

        # Update indent level for following lines: count { and }
        # Avoid counting braces inside string literals or comments
        clean_code = re.sub(r'"(\\.|[^"\\])*"', '""', stripped)
        clean_code = re.sub(r'//.*', '', clean_code)

        opens = clean_code.count('{')
        closes = clean_code.count('}')
        indent_level = max(0, indent_level + opens - closes)

    result = "\n".join(formatted_lines)
    if result and not result.endswith("\n"):
        result += "\n"
    return result


def format_file(file_path: str, check_only: bool = False) -> Tuple[bool, str]:
    """Returns (changed, message)."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        original = f.read()

    formatted = format_kale_source(original)
    changed = (formatted != original)

    if changed and not check_only:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(formatted)

    return changed, formatted


def run_fmt(paths: List[str], check: bool = False) -> int:
    all_files: List[str] = []
    for path in paths:
        if os.path.isfile(path) and path.endswith(".kl"):
            all_files.append(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".kl"):
                        all_files.append(os.path.join(root, file))

    if not all_files:
        print("No .kl files found to format.")
        return 0

    changed_count = 0
    for fpath in all_files:
        changed, _ = format_file(fpath, check_only=check)
        if changed:
            changed_count += 1
            action = "would be reformatted" if check else "reformatted"
            print(f"{action}: {fpath}")

    if check:
        if changed_count > 0:
            print(f"\n{changed_count} file(s) would be reformatted.")
            return 1
        print(f"All {len(all_files)} file(s) already formatted.")
        return 0

    print(f"Formatted {len(all_files)} file(s), {changed_count} modified.")
    return 0
