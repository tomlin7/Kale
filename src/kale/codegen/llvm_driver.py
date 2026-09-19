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

    def _find_msvc_lib_dirs(self) -> list[str]:
        dirs = []
        # Find MSVC lib dir
        msvc_base = r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC"
        if os.path.isdir(msvc_base):
            for v in sorted(os.listdir(msvc_base), reverse=True):
                p = os.path.join(msvc_base, v, "lib", "x64")
                if os.path.isdir(p):
                    dirs.append(p)
                    break
        # Find Windows SDK lib dirs
        sdk_base = r"C:\Program Files (x86)\Windows Kits\10\Lib"
        if os.path.isdir(sdk_base):
            for v in sorted(os.listdir(sdk_base), reverse=True):
                um = os.path.join(sdk_base, v, "um", "x64")
                ucrt = os.path.join(sdk_base, v, "ucrt", "x64")
                if os.path.isdir(um) and os.path.isdir(ucrt):
                    dirs.extend([um, ucrt])
                    break
        return dirs

    def _find_msvc_include_dirs(self) -> list[str]:
        dirs = []
        msvc_base = r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC"
        if os.path.isdir(msvc_base):
            for v in sorted(os.listdir(msvc_base), reverse=True):
                p = os.path.join(msvc_base, v, "include")
                if os.path.isdir(p):
                    dirs.append(p)
                    break
        sdk_base = r"C:\Program Files (x86)\Windows Kits\10\Include"
        if os.path.isdir(sdk_base):
            for v in sorted(os.listdir(sdk_base), reverse=True):
                ucrt = os.path.join(sdk_base, v, "ucrt")
                if os.path.isdir(ucrt):
                    dirs.append(ucrt)
                    break
        return dirs


    def compile_ll(
        self,
        ll_path: str,
        output_path: str | None = None,
        opt_level: int = 2,
        extra_libs: list[str] | None = None,
        lib_dirs: list[str] | None = None,
    ) -> str:
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
        all_lib_dirs = list(lib_dirs or [])

        if is_windows:
            cmd.extend(["--target=x86_64-pc-windows-msvc", "-fuse-ld=lld", "-luser32", "-lgdi32", "-lkernel32", "-lshell32"])
            for msvc_dir in self._find_msvc_lib_dirs():
                if msvc_dir not in all_lib_dirs:
                    all_lib_dirs.append(msvc_dir)
        else:
            cmd.append("-lm")

        for d in all_lib_dirs:
            cmd.append(f"-L{d}" if not d.startswith("-L") else d)

        if extra_libs:
            for lib in extra_libs:
                cmd.append(f"-l{lib}" if not lib.startswith("-l") else lib)

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            err_msg = f"STDERR:\n{result.stderr}\nSTDOUT:\n{result.stdout}"
            raise RuntimeError(f"Clang LLVM compilation failed:\n{err_msg}")

        return output_path

    def run(self, executable_path: str, args: list[str] | None = None) -> subprocess.CompletedProcess:
        cmd = [os.path.abspath(executable_path)] + (args or [])
        return subprocess.run(cmd, capture_output=True, text=True)
