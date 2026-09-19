"""Project bootstrapping and initialization for Kale projects (`kale new` & `kale init`)."""

import os
import re
from typing import Optional
from .manifest import Manifest

VALID_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

GITIGNORE_TEMPLATE = """# Build outputs & temporary artifacts
bin/
dist/
*.tmp.*
*.ll
*.o
*.exe
*.kale-pkg
*.sha256
.kale/
"""

MAIN_KL_TEMPLATE = """// {name} entry point

print("Hello from {name}!");
"""

LIB_KL_TEMPLATE = """// {name} library module

int add(int a, int b) {
    return a + b;
}
"""

README_TEMPLATE = """# {name}

{description}

## Getting Started

### Build
```bash
kale build
```

### Run
```bash
kale run
```
"""


def _sanitize_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "-", name).strip("-")
    return cleaned or "kale_project"


def create_project(
    name: str,
    target_dir: Optional[str] = None,
    is_lib: bool = False,
    description: str = "",
) -> str:
    """Creates a new Kale project directory with kale.toml, entry source, .gitignore, and README.md."""
    if not VALID_NAME_PATTERN.match(name):
        raise ValueError(f"Invalid project name '{name}'. Only alphanumeric characters, dashes, and underscores are allowed.")

    dest = os.path.abspath(target_dir or os.path.join(".", name))

    if os.path.exists(dest):
        if os.path.isdir(dest) and os.listdir(dest):
            raise FileExistsError(f"Destination directory '{dest}' already exists and is not empty.")
    else:
        os.makedirs(dest, exist_ok=True)

    src_dir = os.path.join(dest, "src")
    os.makedirs(src_dir, exist_ok=True)

    desc = description or (f"A Kale library" if is_lib else f"A Kale application")
    entry_rel = "src/lib.kl" if is_lib else "src/main.kl"
    entry_path = os.path.join(dest, entry_rel)

    # Write entry source file
    if is_lib:
        entry_content = LIB_KL_TEMPLATE.replace("{name}", name)
    else:
        entry_content = MAIN_KL_TEMPLATE.replace("{name}", name)

    with open(entry_path, "w", encoding="utf-8") as f:
        f.write(entry_content)

    # Write .gitignore
    gitignore_path = os.path.join(dest, ".gitignore")
    with open(gitignore_path, "w", encoding="utf-8") as f:
        f.write(GITIGNORE_TEMPLATE)

    # Write README.md
    readme_path = os.path.join(dest, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(README_TEMPLATE.replace("{name}", name).replace("{description}", desc))

    # Construct and save kale.toml
    scripts = {
        "build": "kale build",
    }
    if not is_lib:
        scripts["start"] = f"kale run {entry_rel}"
        scripts["test"] = "kale check"

    manifest = Manifest(
        name=name,
        version="0.1.0",
        description=desc,
        authors=[],
        license="MIT",
        edition="2026",
        entry=entry_rel,
        dependencies={},
        dev_dependencies={},
        scripts=scripts,
        build_backend="llvm",
        build_opt=2,
        build_output=None if is_lib else f"bin/{name}",
        build_libs=[],
        build_lib_dirs=[],
        build_includes=[],
        manifest_path=os.path.join(dest, "kale.toml"),
    )
    manifest.save()

    return dest


def init_project(
    dir_path: str = ".",
    is_lib: bool = False,
    name: Optional[str] = None,
    description: str = "",
) -> str:
    """Initializes kale.toml in an existing directory."""
    dest = os.path.abspath(dir_path)
    os.makedirs(dest, exist_ok=True)

    manifest_file = os.path.join(dest, "kale.toml")
    if os.path.isfile(manifest_file):
        raise FileExistsError(f"A kale.toml manifest already exists in '{dest}'.")

    proj_name = name or _sanitize_name(os.path.basename(dest))
    desc = description or (f"A Kale library" if is_lib else f"A Kale application")
    entry_rel = "src/lib.kl" if is_lib else "src/main.kl"
    src_dir = os.path.join(dest, "src")
    os.makedirs(src_dir, exist_ok=True)

    # If neither main.kl nor lib.kl exists, create one
    main_path = os.path.join(src_dir, "main.kl")
    lib_path = os.path.join(src_dir, "lib.kl")
    if not os.path.isfile(main_path) and not os.path.isfile(lib_path):
        target_entry_path = os.path.join(dest, entry_rel)
        template = LIB_KL_TEMPLATE if is_lib else MAIN_KL_TEMPLATE
        with open(target_entry_path, "w", encoding="utf-8") as f:
            f.write(template.replace("{name}", proj_name))
    elif os.path.isfile(lib_path) and not os.path.isfile(main_path):
        entry_rel = "src/lib.kl"
    elif os.path.isfile(main_path):
        entry_rel = "src/main.kl"

    # .gitignore if missing
    gitignore_path = os.path.join(dest, ".gitignore")
    if not os.path.isfile(gitignore_path):
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(GITIGNORE_TEMPLATE)

    # README.md if missing
    readme_path = os.path.join(dest, "README.md")
    if not os.path.isfile(readme_path):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(README_TEMPLATE.replace("{name}", proj_name).replace("{description}", desc))

    scripts = {"build": "kale build"}
    if not is_lib:
        scripts["start"] = f"kale run {entry_rel}"
        scripts["test"] = "kale check"

    manifest = Manifest(
        name=proj_name,
        version="0.1.0",
        description=desc,
        authors=[],
        license="MIT",
        edition="2026",
        entry=entry_rel,
        dependencies={},
        dev_dependencies={},
        scripts=scripts,
        build_backend="llvm",
        build_opt=2,
        build_output=None if is_lib else f"bin/{proj_name}",
        build_libs=[],
        build_lib_dirs=[],
        build_includes=[],
        manifest_path=manifest_file,
    )
    manifest.save()

    return manifest_file
