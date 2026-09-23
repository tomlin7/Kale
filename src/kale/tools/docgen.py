"""Comprehensive API documentation generator for Kale packages and source files."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def generate_docs(source_dir: str, output_dir: str = "docs/api", format_type: str = "markdown") -> int:
    src_path = Path(source_dir)
    if not src_path.exists():
        print(f"Error: Source directory '{source_dir}' does not exist.", file=sys.stderr)
        return 1

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    kl_files = list(src_path.glob("**/*.kl")) if src_path.is_dir() else [src_path]
    print(f"\033[1;34m[kale docgen]\033[0m Found {len(kl_files)} Kale source files in {source_dir}")

    total_structs = 0
    total_fns = 0

    index_lines = [
        f"# {src_path.name.upper()} API Reference",
        "",
        "> Auto-generated API documentation produced by `kale docgen`.",
        "",
        "## Modules",
        "",
    ]

    for f in sorted(kl_files):
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue

        rel_name = f.relative_to(src_path) if src_path.is_dir() else f.name
        mod_title = str(rel_name).replace("\\", "/")

        struct_matches = re.findall(r"struct\s+([A-Za-z0-9_]+)\s*\{([^}]*)\}", content)
        fn_matches = re.findall(r"fn\s+([A-Za-z0-9_<>*]+)\s+([A-Za-z0-9_.]+)\s*\(([^)]*)\)", content)

        total_structs += len(struct_matches)
        total_fns += len(fn_matches)

        file_doc_lines = [
            f"# Module `{mod_title}`",
            "",
            f"*Source file: `{rel_name}`*",
            "",
        ]

        # Extract file header comment
        header_comments = []
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("//"):
                header_comments.append(line[2:].strip())
            elif line:
                break
        if header_comments:
            file_doc_lines.extend(["> " + " ".join(header_comments), ""])

        if struct_matches:
            file_doc_lines.append("## Structs\n")
            for s_name, s_body in struct_matches:
                file_doc_lines.append(f"### `struct {s_name}`\n")
                file_doc_lines.append("```kl")
                file_doc_lines.append(f"struct {s_name} {{")
                for field in s_body.strip().split(";"):
                    field = field.strip()
                    if field:
                        file_doc_lines.append(f"    {field};")
                file_doc_lines.append("}")
                file_doc_lines.append("```\n")

        if fn_matches:
            file_doc_lines.append("## Functions & Methods\n")
            for ret_type, fn_name, params in fn_matches:
                file_doc_lines.append(f"### `{fn_name}`\n")
                file_doc_lines.append("```kl")
                file_doc_lines.append(f"fn {ret_type} {fn_name}({params})")
                file_doc_lines.append("```\n")

        # Write module markdown
        out_file = out_path / f"{f.stem}.md"
        out_file.write_text("\n".join(file_doc_lines), encoding="utf-8")
        index_lines.append(f"- [{mod_title}]({f.stem}.md) — *{len(struct_matches)} structs, {len(fn_matches)} functions*")

    # Write index.md
    index_lines.extend([
        "",
        "---",
        f"**Summary**: Generated documentation for {len(kl_files)} files, {total_structs} structs, {total_fns} functions.",
    ])
    (out_path / "README.md").write_text("\n".join(index_lines), encoding="utf-8")

    print(f"\033[1;32m[kale docgen]\033[0m Successfully wrote {len(kl_files) + 1} documentation files to '{output_dir}'.")
    return 0
