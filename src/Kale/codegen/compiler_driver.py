import os
import shutil
import subprocess
import platform

class CompilerDriver:
    """Manages C compiler invocation (gcc, clang, or cl) and executable generation."""
    def __init__(self, compiler_override: str | None = None):
        self.compiler = compiler_override or self._find_compiler()

    def _find_compiler(self) -> str | None:
        for candidate in ["gcc", "clang", "cl"]:
            path = shutil.which(candidate)
            if path:
                return candidate
        return None

    def compile(self, c_source_path: str, output_path: str | None = None) -> str:
        if not self.compiler:
            raise RuntimeError("No C compiler (gcc, clang, or cl) found in PATH. Please install GCC or Clang.")

        base, _ = os.path.splitext(c_source_path)
        is_windows = (platform.system() == "Windows")

        if output_path is None:
            output_path = f"{base}.exe" if is_windows else base

        cmd: list[str] = []
        if self.compiler in ("gcc", "clang"):
            cmd = [self.compiler, c_source_path, "-o", output_path, "-lm"]
        elif self.compiler == "cl":
            cmd = ["cl", "/nologo", c_source_path, f"/Fe:{output_path}"]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"C compilation failed:\n{result.stderr or result.stdout}")

        return output_path

    def run(self, executable_path: str, args: list[str] | None = None) -> subprocess.CompletedProcess:
        cmd = [os.path.abspath(executable_path)] + (args or [])
        return subprocess.run(cmd, capture_output=True, text=True)
