"""Manifest parser, serializer, and data model for `kale.toml`."""

import os
import sys
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # Handled with fallback if needed


def find_manifest(start_dir: Optional[str] = None) -> Optional[str]:
    """Walks upwards from start_dir to find `kale.toml`."""
    if start_dir is None:
        start_dir = os.getcwd()
    current = os.path.abspath(start_dir)
    if os.path.isfile(current):
        current = os.path.dirname(current)
    while True:
        candidate = os.path.join(current, "kale.toml")
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def serialize_toml_value(val: Any) -> str:
    """Serializes Python primitives into standard TOML value syntax."""
    if isinstance(val, bool):
        return "true" if val else "false"
    elif isinstance(val, int):
        return str(val)
    elif isinstance(val, float):
        return str(val)
    elif isinstance(val, str):
        escaped = (
            val.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )
        return f'"{escaped}"'
    elif isinstance(val, list):
        items = [serialize_toml_value(item) for item in val]
        return f"[{', '.join(items)}]"
    elif isinstance(val, dict):
        items = [f"{k} = {serialize_toml_value(v)}" for k, v in val.items()]
        return f"{{ {', '.join(items)} }}"
    else:
        return f'"{str(val)}"'


@dataclass
class Manifest:
    name: str = "unnamed"
    version: str = "0.1.0"
    description: str = ""
    authors: List[str] = field(default_factory=list)
    license: str = "MIT"
    edition: str = "2026"
    entry: str = "src/main.kl"
    dependencies: Dict[str, Union[str, Dict[str, Any]]] = field(default_factory=dict)
    dev_dependencies: Dict[str, Union[str, Dict[str, Any]]] = field(default_factory=dict)
    scripts: Dict[str, str] = field(default_factory=dict)
    build_backend: str = "llvm"
    build_opt: int = 2
    build_output: Optional[str] = None
    build_libs: List[str] = field(default_factory=list)
    build_lib_dirs: List[str] = field(default_factory=list)
    build_includes: List[str] = field(default_factory=list)
    extra_sections: Dict[str, Any] = field(default_factory=dict)
    manifest_path: str = ""

    @property
    def project_dir(self) -> str:
        if self.manifest_path:
            return os.path.dirname(os.path.abspath(self.manifest_path))
        return os.path.abspath(".")

    @classmethod
    def load(cls, path: str) -> "Manifest":
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Manifest file not found: {path}")

        if tomllib is not None:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        else:
            # Fallback basic TOML reader
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            raise RuntimeError(f"tomllib not available to parse TOML in {path}")

        return cls.from_dict(data, manifest_path=path)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], manifest_path: str = "") -> "Manifest":
        package = data.get("package", {})
        build = data.get("build", {})

        deps = data.get("dependencies", {})
        dev_deps = data.get("dev-dependencies", data.get("dev_dependencies", {}))
        scripts = data.get("scripts", {})

        known_sections = {"package", "dependencies", "dev-dependencies", "dev_dependencies", "scripts", "build"}
        extra = {k: v for k, v in data.items() if k not in known_sections}

        entry = package.get("entry")
        if not entry:
            proj_dir = os.path.dirname(os.path.abspath(manifest_path)) if manifest_path else os.getcwd()
            if os.path.isfile(os.path.join(proj_dir, "src", "lib.kl")) and not os.path.isfile(os.path.join(proj_dir, "src", "main.kl")):
                entry = "src/lib.kl"
            else:
                entry = "src/main.kl"

        return cls(
            name=package.get("name", "unnamed"),
            version=str(package.get("version", "0.1.0")),
            description=package.get("description", ""),
            authors=package.get("authors", []),
            license=package.get("license", "MIT"),
            edition=str(package.get("edition", "2026")),
            entry=entry,
            dependencies=deps,
            dev_dependencies=dev_deps,
            scripts=scripts,
            build_backend=build.get("backend", "llvm"),
            build_opt=int(build.get("opt", 2)),
            build_output=build.get("output"),
            build_libs=build.get("libs", []),
            build_lib_dirs=build.get("lib-dirs", build.get("lib_dirs", [])),
            build_includes=build.get("includes", []),
            extra_sections=extra,
            manifest_path=manifest_path,
        )

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "package": {
                "name": self.name,
                "version": self.version,
                "description": self.description,
                "authors": self.authors,
                "license": self.license,
                "edition": self.edition,
                "entry": self.entry,
            },
            "dependencies": self.dependencies,
            "dev-dependencies": self.dev_dependencies,
            "scripts": self.scripts,
            "build": {
                "backend": self.build_backend,
                "opt": self.build_opt,
                "libs": self.build_libs,
                "lib-dirs": self.build_lib_dirs,
                "includes": self.build_includes,
            },
        }
        if self.build_output is not None:
            d["build"]["output"] = self.build_output
        d.update(self.extra_sections)
        return d

    def to_toml(self) -> str:
        lines: List[str] = []

        # [package]
        lines.append("[package]")
        lines.append(f"name = {serialize_toml_value(self.name)}")
        lines.append(f"version = {serialize_toml_value(self.version)}")
        if self.description:
            lines.append(f"description = {serialize_toml_value(self.description)}")
        lines.append(f"authors = {serialize_toml_value(self.authors)}")
        lines.append(f"license = {serialize_toml_value(self.license)}")
        lines.append(f"edition = {serialize_toml_value(self.edition)}")
        lines.append(f"entry = {serialize_toml_value(self.entry)}")
        lines.append("")

        # [dependencies]
        lines.append("[dependencies]")
        for dep_name, dep_spec in sorted(self.dependencies.items()):
            lines.append(f"{dep_name} = {serialize_toml_value(dep_spec)}")
        lines.append("")

        # [dev-dependencies]
        lines.append("[dev-dependencies]")
        for dep_name, dep_spec in sorted(self.dev_dependencies.items()):
            lines.append(f"{dep_name} = {serialize_toml_value(dep_spec)}")
        lines.append("")

        # [scripts]
        lines.append("[scripts]")
        for script_name, cmd in self.scripts.items():
            lines.append(f"{script_name} = {serialize_toml_value(cmd)}")
        lines.append("")

        # [build]
        lines.append("[build]")
        lines.append(f"backend = {serialize_toml_value(self.build_backend)}")
        lines.append(f"opt = {serialize_toml_value(self.build_opt)}")
        if self.build_output:
            lines.append(f"output = {serialize_toml_value(self.build_output)}")
        lines.append(f"libs = {serialize_toml_value(self.build_libs)}")
        lines.append(f"lib-dirs = {serialize_toml_value(self.build_lib_dirs)}")
        lines.append(f"includes = {serialize_toml_value(self.build_includes)}")
        lines.append("")

        # Extra sections
        for sec_name, sec_val in self.extra_sections.items():
            if isinstance(sec_val, dict):
                lines.append(f"[{sec_name}]")
                for k, v in sec_val.items():
                    lines.append(f"{k} = {serialize_toml_value(v)}")
                lines.append("")

        return "\n".join(lines).strip() + "\n"

    def save(self, path: Optional[str] = None):
        target_path = path or self.manifest_path
        if not target_path:
            target_path = os.path.join(os.getcwd(), "kale.toml")
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(self.to_toml())
        self.manifest_path = target_path

    def add_dependency(self, name: str, spec: Union[str, Dict[str, Any]], dev: bool = False):
        if dev:
            self.dev_dependencies[name] = spec
        else:
            self.dependencies[name] = spec

    def remove_dependency(self, name: str) -> bool:
        removed = False
        if name in self.dependencies:
            del self.dependencies[name]
            removed = True
        if name in self.dev_dependencies:
            del self.dev_dependencies[name]
            removed = True
        return removed

    def get_all_include_dirs(
        self,
        base_dir: Optional[str] = None,
        visited: Optional[set[str]] = None,
        include_dev: bool = False,
    ) -> List[str]:
        """Resolves all include directories for compilation, including src and transitive path dependencies."""
        root = os.path.abspath(base_dir or self.project_dir)
        if visited is None:
            visited = set()

        if root in visited:
            return []
        visited.add(root)

        includes: List[str] = []

        # Project src directory
        src_dir = os.path.join(root, "src")
        if os.path.isdir(src_dir) and src_dir not in includes:
            includes.append(src_dir)

        # Configured build.includes
        for inc in self.build_includes:
            abs_inc = os.path.abspath(inc if os.path.isabs(inc) else os.path.join(root, inc))
            if os.path.isdir(abs_inc) and abs_inc not in includes:
                includes.append(abs_inc)

        # Collect dependencies
        dep_dict: Dict[str, Any] = dict(self.dependencies)
        if include_dev:
            dep_dict.update(self.dev_dependencies)

        # Path dependencies (recursively resolve transitive dependencies)
        for dep_name, dep_spec in dep_dict.items():
            if isinstance(dep_spec, dict) and "path" in dep_spec:
                rel_path = dep_spec["path"]
                abs_dep_dir = os.path.abspath(rel_path if os.path.isabs(rel_path) else os.path.join(root, rel_path))
                if os.path.isdir(abs_dep_dir):
                    # Add path dep root
                    if abs_dep_dir not in includes:
                        includes.append(abs_dep_dir)
                    # Add path dep src/ if present
                    dep_src = os.path.join(abs_dep_dir, "src")
                    if os.path.isdir(dep_src) and dep_src not in includes:
                        includes.append(dep_src)
                    # If path dep has kale.toml, load and recursively resolve its dependencies
                    dep_manifest_path = os.path.join(abs_dep_dir, "kale.toml")
                    if os.path.isfile(dep_manifest_path):
                        try:
                            dep_manifest = Manifest.load(dep_manifest_path)
                            transitive = dep_manifest.get_all_include_dirs(
                                base_dir=abs_dep_dir,
                                visited=visited,
                                include_dev=False,
                            )
                            for t_inc in transitive:
                                if t_inc not in includes:
                                    includes.append(t_inc)
                        except Exception:
                            pass

        return includes
