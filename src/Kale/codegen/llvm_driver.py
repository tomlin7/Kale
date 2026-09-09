import os
import shutil
import subprocess
import platform

class LLVMDriver:
    """Compiles LLVM IR (.ll) files into native executables using Clang/LLD."""
    def __init__(self, clang_path: str | None = None):
        self.clang_path = clang_path or self._find_clang()

    def _find_clang(self) -> str | None:
        path = shutil.which("clang")
        if path:
            return path
        # Common locations on Windows
        vs_clang = r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\Llvm\bin\clang.exe"
        if os.path.isfile(vs_clang):
            return vs_clang
        return None

    def compile_ll(self, ll_path: str, output_path: str | None = None, opt_level: int = 2) -> str:
        if not self.clang_path:
            raise RuntimeError("Clang compiler not found in PATH. Please install Clang or LLVM.")

        base, _ = os.path.splitext(ll_path)
        is_windows = (platform.system() == "Windows")

        if output_path is None:
            output_path = f"{base}.exe" if is_windows else base

        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        cmd = [self.clang_path, ll_path, f"-O{opt_level}", "-o", output_path]
        if is_windows:
            cmd.append("--target=x86_64-pc-windows-msvc")
        else:
            cmd.append("-lm")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Clang LLVM compilation failed:\n{result.stderr or result.stdout}")

        return output_path

    def run(self, executable_path: str, args: list[str] | None = None) -> subprocess.CompletedProcess:
        cmd = [os.path.abspath(executable_path)] + (args or [])
        return subprocess.run(cmd, capture_output=True, text=True)
