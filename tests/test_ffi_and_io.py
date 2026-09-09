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


class TestFFIAndIO(unittest.TestCase):
    def test_extern_function_declaration_and_jit(self):
        code = """
extern int abs(int x);
extern int puts(string s);

int run_test() {
    int v = abs(-99);
    return v;
}

return run_test();
"""
        diag = DiagnosticBag()
        text = SourceText(code)
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, [d.message for d in diag])

        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, [d.message for d in diag])

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)
        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 99)

    def test_extern_c_prototype_emission(self):
        code = """
extern int abs(int x);
extern int printf(string fmt, ...);

int foo() {
    return abs(-10);
}
return foo();
"""
        diag = DiagnosticBag()
        text = SourceText(code)
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, [d.message for d in diag])

        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, [d.message for d in diag])

        c_emitter = CEmitter()
        c_code = c_emitter.emit(program)
        self.assertIn("extern long long abs(long long x);", c_code)
        self.assertIn("extern long long printf(const char* fmt, ...);", c_code)
        self.assertIn("long long foo(void) {", c_code)

    def test_std_io_file_module_import_and_file_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file_path = os.path.join(tmpdir, "output.txt").replace("\\", "/")
            code = f"""
import "io/file.kl" as io;

int main_work() {{
    io.File f = io.open("{test_file_path}", "w");
    if (!f.is_open) {{
        return 1;
    }}
    f.write("Kale Monorepo FFI Test\\n");
    f.close();
    return 0;
}}

return main_work();
"""
            diag = DiagnosticBag()
            text = SourceText(code)
            parser = Parser(text, diag)
            unit = parser.parse_compilation_unit()
            self.assertFalse(diag.has_errors, [d.message for d in diag])

            loader = ModuleLoader(diag)
            binder = Binder(diag, module_loader=loader)
            program = binder.bind_program(unit)
            self.assertFalse(diag.has_errors, [d.message for d in diag])

            emitter = LLVMEmitter()
            mod = emitter.emit_module(program)
            jit = LLVMJIT()
            ret = jit.run_ir(str(mod))
            self.assertEqual(ret, 0)

            # Verify the file was written to disk
            actual_path = os.path.join(tmpdir, "output.txt")
            self.assertTrue(os.path.isfile(actual_path))
            with open(actual_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertEqual(content, "Kale Monorepo FFI Test\n")

    def test_std_sys_process_module_import(self):
        code = """
import "sys/process.kl" as proc;

int check_exec() {
    string path_val = proc.env("PATH");
    if (path_val == "") {
        return 1;
    }
    return 0;
}

return check_exec();
"""
        diag = DiagnosticBag()
        text = SourceText(code)
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, [d.message for d in diag])

        loader = ModuleLoader(diag)
        binder = Binder(diag, module_loader=loader)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, [d.message for d in diag])

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)
        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 0)


if __name__ == "__main__":
    unittest.main()
