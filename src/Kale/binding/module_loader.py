import os
from typing import Dict, List, Set, Optional, Tuple
from ..diagnostics.source_text import SourceText
from ..diagnostics.diagnostic_bag import DiagnosticBag
from ..diagnostics.text_span import TextSpan
from ..parser.parser import Parser
from ..ast.nodes import CompilationUnit, ImportStatement, FromImportStatement

class ModuleLoader:
    """Manages file path resolution, cycle detection, and parsing across multiple Kale source modules."""
    def __init__(self, diagnostics: DiagnosticBag, search_paths: Optional[List[str]] = None):
        self.diagnostics = diagnostics
        self.search_paths: List[str] = [os.path.abspath(p) for p in (search_paths or [])]

        # Auto-discover monorepo packages and libs paths relative to this package installation
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # src/Kale/binding -> src/Kale -> src -> repo_root
        repo_root = os.path.dirname(repo_root)
        for auto_dir in [
            os.path.join(repo_root, "packages", "std"),
            os.path.join(repo_root, "packages"),
            os.path.join(repo_root, "libs"),
            repo_root,
        ]:
            if os.path.isdir(auto_dir) and os.path.abspath(auto_dir) not in self.search_paths:
                self.search_paths.append(os.path.abspath(auto_dir))

        # Always include environment variable KALE_PATH if present
        if "KALE_PATH" in os.environ:
            for p in os.environ["KALE_PATH"].split(os.pathsep):
                if p and os.path.isdir(p):
                    self.search_paths.append(os.path.abspath(p))

        self._parsed_units: Dict[str, CompilationUnit] = {}
        self._source_texts: Dict[str, SourceText] = {}
        self._import_chain: List[str] = []
        self._bound_modules: Dict[str, Tuple[str, Any]] = {}
        self._binding_chain: List[str] = []

    def get_source_text(self, normalized_path: str) -> Optional[SourceText]:
        return self._source_texts.get(normalized_path)

    def load_module(self, relative_path: str, importing_file: Optional[str] = None, span: Optional[TextSpan] = None) -> Tuple[Optional[str], Optional[CompilationUnit]]:
        """
        Resolves relative_path relative to importing_file or configured search_paths,
        parses it, checks for cycles, and returns (normalized_path, compilation_unit).
        """
        target_path: Optional[str] = None

        # 1. Resolve relative to importing file
        if importing_file:
            base_dir = os.path.dirname(os.path.abspath(importing_file))
            candidate = os.path.normpath(os.path.join(base_dir, relative_path))
            if os.path.isfile(candidate):
                target_path = candidate
        else:
            candidate = os.path.normpath(os.path.abspath(relative_path))
            if os.path.isfile(candidate):
                target_path = candidate

        # 2. If not found and path is not explicit relative (./ or ../), check search_paths
        if target_path is None and not relative_path.startswith(("./", "../", ".\\", "..\\")):
            for sp_dir in self.search_paths:
                candidate = os.path.normpath(os.path.join(sp_dir, relative_path))
                if os.path.isfile(candidate):
                    target_path = candidate
                    break

        # Check existence
        if target_path is None or not os.path.isfile(target_path):
            sp = span or TextSpan(0, 0)
            self.diagnostics.report(sp, f"Cannot find module file '{relative_path}'.")
            return None, None

        # Cycle detection
        if target_path in self._import_chain:
            cycle_str = " -> ".join([os.path.basename(p) for p in self._import_chain] + [os.path.basename(target_path)])
            sp = span or TextSpan(0, 0)
            self.diagnostics.report(sp, f"Circular import dependency detected: {cycle_str}.")
            return None, None

        # Return cached if already parsed
        if target_path in self._parsed_units:
            return target_path, self._parsed_units[target_path]

        # Read source
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                code = f.read()
        except Exception as e:
            sp = span or TextSpan(0, 0)
            self.diagnostics.report(sp, f"Error reading module file '{relative_path}': {e}")
            return None, None

        source_text = SourceText(code, file_name=target_path)
        self._source_texts[target_path] = source_text

        parser = Parser(source_text, self.diagnostics)
        unit = parser.parse_compilation_unit()
        self._parsed_units[target_path] = unit

        # Recursively discover and parse any imports in this unit
        self._import_chain.append(target_path)
        for stmt in unit.statements:
            if isinstance(stmt, (ImportStatement, FromImportStatement)):
                sub_path = str(stmt.module_path_token.value)
                self.load_module(sub_path, importing_file=target_path, span=stmt.module_path_token.span)
        self._import_chain.pop()

        return target_path, unit

    def get_all_loaded_units(self) -> Dict[str, CompilationUnit]:
        return dict(self._parsed_units)
