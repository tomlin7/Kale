"""
src/kale/tools/doc.py
Documentation generator for Kale codebases.
Extracts doc comments, struct definitions, function signatures, and methods,
producing static Markdown and HTML documentation.
"""

import os
import re
from typing import List, Dict, Any

class DocItem:
    def __init__(self, kind: str, name: str, signature: str, doc: str, file_path: str, line: int):
        self.kind = kind          # "fn", "struct", "method", "enum", "extern"
        self.name = name
        self.signature = signature
        self.doc = doc.strip()
        self.file_path = file_path
        self.line = line


def parse_doc_items(file_path: str, content: str) -> List[DocItem]:
    items: List[DocItem] = []
    lines = content.splitlines()

    pending_doc: List[str] = []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Doc comment accumulator
        if stripped.startswith("///"):
            pending_doc.append(stripped[3:].strip())
            continue
        elif stripped.startswith("//") and not stripped.startswith("// ──"):
            # Normal comment preceding a definition
            pending_doc.append(stripped[2:].strip())
            continue

        doc_str = "\n".join(pending_doc)

        # 1. Struct: struct Name {
        struct_m = re.match(r'struct\s+([A-Za-z0-9_]+)\s*\{?', stripped)
        if struct_m:
            sname = struct_m.group(1)
            items.append(DocItem("struct", sname, f"struct {sname}", doc_str, file_path, i))
            pending_doc = []
            continue

        # 2. Method: fn ReturnType StructName.method_name(...)
        method_m = re.match(r'fn\s+([A-Za-z0-9_\*]+)\s+([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)\s*\(([^)]*)\)', stripped)
        if method_m:
            ret = method_m.group(1)
            struct_name = method_m.group(2)
            meth_name = method_m.group(3)
            params = method_m.group(4)
            sig = f"fn {ret} {struct_name}.{meth_name}({params})"
            items.append(DocItem("method", f"{struct_name}.{meth_name}", sig, doc_str, file_path, i))
            pending_doc = []
            continue

        # 3. Function: fn ReturnType func_name(...)
        fn_m = re.match(r'fn\s+([A-Za-z0-9_\*]+)\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)', stripped)
        if fn_m:
            ret = fn_m.group(1)
            fn_name = fn_m.group(2)
            params = fn_m.group(3)
            sig = f"fn {ret} {fn_name}({params})"
            items.append(DocItem("fn", fn_name, sig, doc_str, file_path, i))
            pending_doc = []
            continue

        # 4. Extern: extern ReturnType func_name(...);
        ext_m = re.match(r'extern\s+([A-Za-z0-9_\*]+)\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)', stripped)
        if ext_m:
            ret = ext_m.group(1)
            ext_name = ext_m.group(2)
            params = ext_m.group(3)
            sig = f"extern {ret} {ext_name}({params});"
            items.append(DocItem("extern", ext_name, sig, doc_str, file_path, i))
            pending_doc = []
            continue

        # Reset pending doc if line is not empty and not matched
        if stripped:
            pending_doc = []

    return items


def generate_markdown_docs(items_by_file: Dict[str, List[DocItem]], title: str = "Kale API Documentation") -> str:
    md = [f"# {title}\n"]

    for file_path, items in items_by_file.items():
        if not items:
            continue
        rel_path = os.path.relpath(file_path, ".")
        md.append(f"## Module: `{rel_path}`\n")

        structs = [it for it in items if it.kind == "struct"]
        methods = [it for it in items if it.kind == "method"]
        functions = [it for it in items if it.kind in ("fn", "extern")]

        if structs:
            md.append("### Structs\n")
            for s in structs:
                md.append(f"#### `{s.name}`\n")
                md.append(f"```kale\n{s.signature}\n```\n")
                if s.doc:
                    md.append(f"{s.doc}\n")

                # List methods under this struct
                struct_methods = [m for m in methods if m.name.startswith(f"{s.name}.")]
                if struct_methods:
                    md.append("**Methods:**\n")
                    for m in struct_methods:
                        md.append(f"- `{m.signature}`")
                        if m.doc:
                            md.append(f"  \n  {m.doc}")
                    md.append("")

        if functions:
            md.append("### Functions\n")
            for f in functions:
                md.append(f"#### `{f.name}`\n")
                md.append(f"```kale\n{f.signature}\n```\n")
                if f.doc:
                    md.append(f"{f.doc}\n")

        md.append("---\n")

    return "\n".join(md)


def run_doc(paths: List[str], out_file: str = "docs/API.md") -> int:
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
        print("No .kl files found to document.")
        return 0

    items_by_file: Dict[str, List[DocItem]] = {}
    total_items = 0

    for fpath in all_files:
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            items = parse_doc_items(fpath, content)
            if items:
                items_by_file[fpath] = items
                total_items += len(items)
        except Exception as e:
            print(f"Error parsing {fpath}: {e}")

    md_content = generate_markdown_docs(items_by_file)

    out_dir = os.path.dirname(out_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Generated documentation for {total_items} items across {len(items_by_file)} files -> '{out_file}'")
    return 0
