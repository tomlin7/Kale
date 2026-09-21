"""
src/kale/tools/lint.py
Static analyzer and linter for Kale (.kl) codebases.
Detects:
- Tabs used for indentation
- Lines exceeding 120 characters
- Trailing whitespace
- Unused imported module aliases
- Naming convention violations (Structs vs functions)
- alloc/free mismatch heuristics
"""

import os
import re
from typing import List, Dict, Any

class LintIssue:
    def __init__(self, file_path: str, line: int, col: int, code: str, message: str, severity: str = "warning"):
        self.file_path = file_path
        self.line = line
        self.col = col
        self.code = code
        self.message = message
        self.severity = severity

    def __str__(self) -> str:
        prefix = f"[{self.severity.upper()}]"
        return f"{self.file_path}:{self.line}:{self.col}: {prefix} {self.code}: {self.message}"


def lint_source(file_path: str, content: str) -> List[LintIssue]:
    issues: List[LintIssue] = []
    lines = content.splitlines()

    imports: Dict[str, int] = {}  # alias -> line_num

    # Heuristic tracking
    alloc_count = 0
    free_count = 0

    for i, line in enumerate(lines, 1):
        # Rule: Trailing whitespace
        if line.endswith(" ") or line.endswith("\t"):
            issues.append(LintIssue(file_path, i, len(line), "W001", "Trailing whitespace detected"))

        # Rule: Tab characters
        if "\t" in line:
            issues.append(LintIssue(file_path, i, line.find("\t") + 1, "W002", "Tab character used instead of 4 spaces"))

        # Rule: Line length
        if len(line) > 120:
            issues.append(LintIssue(file_path, i, 121, "W003", f"Line exceeds 120 characters ({len(line)} chars)"))

        # Find imports: import "..." as alias;
        imp_match = re.search(r'import\s+["\'][^"\']+["\']\s+as\s+([A-Za-z0-9_]+)\s*;', line)
        if imp_match:
            alias = imp_match.group(1)
            imports[alias] = i

        # Rule: Struct naming (should start with capital letter)
        struct_match = re.search(r'\bstruct\s+([A-Za-z0-9_]+)', line)
        if struct_match:
            sname = struct_match.group(1)
            if not sname[0].isupper():
                issues.append(LintIssue(file_path, i, struct_match.start(1) + 1, "C001", f"Struct name '{sname}' should be PascalCase", "convention"))

        # Track alloc/free heuristics
        if "alloc(" in line:
            alloc_count += line.count("alloc(")
        if "free(" in line:
            free_count += line.count("free(")

    # Check for unused imports
    clean_text = re.sub(r'import\s+["\'][^"\']+["\']\s+as\s+[A-Za-z0-9_]+\s*;', '', content)
    for alias, line_num in imports.items():
        # Look for usage of alias.something
        usage = re.search(r'\b' + re.escape(alias) + r'\.', clean_text)
        if not usage:
            issues.append(LintIssue(file_path, line_num, 1, "W004", f"Imported module alias '{alias}' is never used"))

    # Check alloc vs free heuristic
    if alloc_count > 0 and free_count == 0:
        issues.append(LintIssue(file_path, 1, 1, "M001", f"File contains {alloc_count} dynamic allocation(s) ('alloc') but no calls to 'free'", "warning"))

    return issues


def run_lint(paths: List[str]) -> int:
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
        print("No .kl files found to lint.")
        return 0

    total_issues = 0
    errors_count = 0

    for fpath in all_files:
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            issues = lint_source(fpath, content)
            for issue in issues:
                print(issue)
                total_issues += 1
                if issue.severity == "error":
                    errors_count += 1
        except Exception as e:
            print(f"Error linting {fpath}: {e}")
            errors_count += 1

    print(f"\nLint complete: {len(all_files)} file(s) checked, {total_issues} issue(s) found.")
    return 1 if errors_count > 0 else 0
