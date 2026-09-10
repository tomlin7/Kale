import unittest
import os
import tempfile
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT
from kale.codegen.c_emitter import CEmitter

class TestStdFs(unittest.TestCase):
    def run_kale_jit(self, code: str):
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

    def test_std_fs_path(self):
        code = """
        import "packages/std/fs/path.kl" as path;

        string p1 = "foo/bar/baz.txt";
        string d = path.dirname(p1);
        string b = path.basename(p1);
        string e = path.ext(p1);
        
        return path.strlen(d) * 1000 + path.strlen(b) * 10 + path.strlen(e);
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 7 * 1000 + 7 * 10 + 4)

    def test_std_fs_file_util(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = os.path.join(tmp_dir, "test.txt").replace("\\", "/")
            code = f"""
            import "packages/std/fs/file_util.kl" as fu;

            string path = "{test_file}";
            bool written = fu.write_string(path, "Hello Kale FS!");
            if (!written) {{
                return 1;
            }}
            bool ex = fu.exists(path);
            if (!ex) {{
                return 2;
            }}
            int sz = fu.file_size(path);
            if (sz != 14) {{
                return 3;
            }}
            bool del = fu.delete_file(path);
            if (!del) {{
                return 4;
            }}
            if (fu.exists(path)) {{
                return 5;
            }}
            return 42;
            """
            res = self.run_kale_jit(code)
            self.assertEqual(res, 42)

    def test_std_fs_dir(self):
        code = """
        import "packages/std/fs/dir.kl" as d;

        List<string> entries = d.list_dir("*.*");
        return entries.size();
        """
        res = self.run_kale_jit(code)
        self.assertGreater(res, 0)

if __name__ == "__main__":
    unittest.main()
