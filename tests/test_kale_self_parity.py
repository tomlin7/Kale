import unittest
import os
import shutil
import subprocess
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestKaleSelfParity(unittest.TestCase):
    """End-to-end verification of language feature parity in pure Kale bootstrapped compiler."""

    def run_kale_jit(self, code: str) -> int:
        st = SourceText(code)
        diag = DiagnosticBag()
        loader = ModuleLoader([os.path.abspath(".")], diag)
        parser = Parser(st, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, f"Parser errors: {[d.message for d in diag]}")

        binder = Binder(diag, module_loader=loader)
        bound = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, f"Binder errors: {[d.message for d in diag]}")

        emitter = LLVMEmitter()
        llvm_mod = emitter.emit_module(bound)
        jit = LLVMJIT()
        return jit.run_ir(str(llvm_mod))

    def test_pure_kale_compiles_struct_methods_and_switch(self):
        code = """
        import "src/kale_self/main.kl" as km;
        extern void* strstr(string haystack, string needle);

        string src = "struct Counter { int val; }\\nfn void Counter.inc(int amt) { this->val = this->val + amt; }\\nfn int main() { Counter c; c.val = 10; c.inc(5); return c.val; }";
        string c_code = km.compile_source(src);
        if ((void*)c_code == (void*)0) { return 1; }

        if (strstr(c_code, "kale_Counter_inc") == (void*)0) { return 2; }
        if (strstr(c_code, "kale_Counter_inc(&c, 5)") == (void*)0) { return 3; }
        return 100;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 100)

    def test_pure_kale_compiles_enum_and_print(self):
        code = """
        import "src/kale_self/main.kl" as km;
        extern void* strstr(string haystack, string needle);

        string src = "enum State { OFF, ON = 1 }\\nfn int main() { int s = ON; print(s); return s; }";
        string c_code = km.compile_source(src);
        if ((void*)c_code == (void*)0) { return 1; }

        if (strstr(c_code, "typedef enum State") == (void*)0) { return 2; }
        if (strstr(c_code, "_kale_print(s)") == (void*)0) { return 3; }
        return 200;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 200)

    def test_pure_kale_compiles_alloc_and_indexing(self):
        code = """
        import "src/kale_self/main.kl" as km;
        extern void* strstr(string haystack, string needle);

        string src = "fn int main() { int* arr = alloc(int, 10); arr[0] = 42; int v = arr[0]; free(arr); return v; }";
        string c_code = km.compile_source(src);
        if ((void*)c_code == (void*)0) { return 1; }

        if (strstr(c_code, "malloc(sizeof(int64_t) * (10))") == (void*)0) { return 2; }
        if (strstr(c_code, "arr[0] = 42;") == (void*)0) { return 3; }
        if (strstr(c_code, "free((void*)(arr));") == (void*)0) { return 4; }
        return 300;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 300)

    def test_kalec_executable_end_to_end(self):
        """Verifies kalec.exe executable CLI options and help output."""
        kalec_exe = os.path.abspath("bin/kalec.exe")
        if not os.path.isfile(kalec_exe):
            self.skipTest("kalec.exe not found")

        help_res = subprocess.run([kalec_exe], capture_output=True, text=True)
        self.assertEqual(help_res.returncode, 0)
        self.assertIn("Kale Self-Hosting Compiler", help_res.stdout)
        self.assertIn("Usage: kalec", help_res.stdout)

    def test_pure_kale_compiles_full_program_to_host_binary(self):
        """Compiles a complete Kale program to C via pure Kale main driver and builds with host C compiler."""
        host_cc = shutil.which("gcc") or shutil.which("clang")
        if not host_cc:
            self.skipTest("No C compiler (gcc/clang) found")

        code = """
        import "src/kale_self/main.kl" as km;

        string src = "struct Point { int x; int y; }\\nfn void Point.set(int nx, int ny) { this->x = nx; this->y = ny; }\\nfn int main() { Point p; p.set(30, 12); return p.x + p.y; }";
        string c_code = km.compile_source(src);
        if ((void*)c_code == (void*)0) { return 1; }

        bool ok = km.write_string_to_file("bin/test_parity_sample.c", c_code);
        if (!ok) { return 2; }
        return 0;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 0)

        c_path = os.path.abspath("bin/test_parity_sample.c")
        exe_path = os.path.abspath("bin/test_parity_sample.exe" if os.name == "nt" else "bin/test_parity_sample")

        try:
            self.assertTrue(os.path.isfile(c_path))
            build_res = subprocess.run([host_cc, c_path, "-o", exe_path], capture_output=True, text=True)
            self.assertEqual(build_res.returncode, 0, f"Host C compiler failed:\n{build_res.stderr}")
            self.assertTrue(os.path.isfile(exe_path))

            run_res = subprocess.run([exe_path])
            self.assertEqual(run_res.returncode, 42)
        finally:
            for p in (c_path, exe_path):
                if os.path.isfile(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass

if __name__ == "__main__":
    unittest.main()
