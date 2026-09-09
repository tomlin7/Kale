import unittest
import os
import io
import sys
import tempfile
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT
from kale.codegen.c_emitter import CEmitter


class TestModules(unittest.TestCase):
    def test_module_import_and_call_jit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            math_path = os.path.join(tmpdir, "math.kl")
            with open(math_path, "w", encoding="utf-8") as f:
                f.write('''int square(int x) { return x * x; }
int cube(int x) { return x * x * x; }
''')

            main_path = os.path.join(tmpdir, "main.kl")
            with open(main_path, "w", encoding="utf-8") as f:
                f.write('''import "math.kl" as m;
int a = m.square(5);
int b = m.cube(3);
print(a, b);
return a + b;
''')

            with open(main_path, "r", encoding="utf-8") as f:
                text = SourceText(f.read(), file_name=main_path)

            diag = DiagnosticBag()
            parser = Parser(text, diag)
            unit = parser.parse_compilation_unit()
            self.assertFalse(diag.has_errors)

            loader = ModuleLoader(diag)
            binder = Binder(diag, module_loader=loader, current_file=main_path)
            program = binder.bind_program(unit)
            if diag.has_errors:
                for d in diag:
                    print("DIAG:", d.message)
            self.assertFalse(diag.has_errors)

            emitter = LLVMEmitter()
            mod = emitter.emit_module(program)
            jit = LLVMJIT()

            ret = jit.run_ir(str(mod))
            self.assertEqual(ret, 52)

    def test_from_import_functions_and_structs_jit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            geo_path = os.path.join(tmpdir, "geo.kl")
            with open(geo_path, "w", encoding="utf-8") as f:
                f.write('''struct Vec2 {
    int x;
    int y;
};

int dot(Vec2 a, Vec2 b) {
    return a.x * b.x + a.y * b.y;
}
''')

            main_path = os.path.join(tmpdir, "main.kl")
            with open(main_path, "w", encoding="utf-8") as f:
                f.write('''from "geo.kl" import Vec2, dot;
Vec2 v1;
v1.x = 3;
v1.y = 4;

Vec2 v2;
v2.x = 2;
v2.y = 5;

int d = dot(v1, v2);
print(d);
return d;
''')

            with open(main_path, "r", encoding="utf-8") as f:
                text = SourceText(f.read(), file_name=main_path)

            diag = DiagnosticBag()
            parser = Parser(text, diag)
            unit = parser.parse_compilation_unit()
            self.assertFalse(diag.has_errors)

            loader = ModuleLoader(diag)
            binder = Binder(diag, module_loader=loader, current_file=main_path)
            program = binder.bind_program(unit)
            self.assertFalse(diag.has_errors)

            emitter = LLVMEmitter()
            mod = emitter.emit_module(program)
            jit = LLVMJIT()

            ret = jit.run_ir(str(mod))
            self.assertEqual(ret, 26)

    def test_circular_import_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a_path = os.path.join(tmpdir, "a.kl")
            b_path = os.path.join(tmpdir, "b.kl")

            with open(a_path, "w", encoding="utf-8") as f:
                f.write('import "b.kl";\nint fa() { return 1; }\n')

            with open(b_path, "w", encoding="utf-8") as f:
                f.write('import "a.kl";\nint fb() { return 2; }\n')

            with open(a_path, "r", encoding="utf-8") as f:
                text = SourceText(f.read(), file_name=a_path)

            diag = DiagnosticBag()
            parser = Parser(text, diag)
            unit = parser.parse_compilation_unit()

            loader = ModuleLoader(diag)
            binder = Binder(diag, module_loader=loader, current_file=a_path)
            binder.bind_program(unit)
            self.assertTrue(diag.has_errors)
            self.assertTrue(any("Circular import" in str(d.message) for d in diag))

    def test_c_emitter_with_modules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            calc_path = os.path.join(tmpdir, "calc.kl")
            with open(calc_path, "w", encoding="utf-8") as f:
                f.write('int sub(int a, int b) { return a - b; }\n')

            main_path = os.path.join(tmpdir, "main.kl")
            with open(main_path, "w", encoding="utf-8") as f:
                f.write('import "calc.kl" as c;\nint diff = c.sub(100, 30);\nprint(diff);\n')

            with open(main_path, "r", encoding="utf-8") as f:
                text = SourceText(f.read(), file_name=main_path)

            diag = DiagnosticBag()
            parser = Parser(text, diag)
            unit = parser.parse_compilation_unit()

            loader = ModuleLoader(diag)
            binder = Binder(diag, module_loader=loader, current_file=main_path)
            program = binder.bind_program(unit)
            self.assertFalse(diag.has_errors)

            emitter = CEmitter()
            c_code = emitter.emit(program)
            self.assertIn("kale_calc_sub", c_code)
            self.assertIn("main(", c_code)

    def test_search_paths_import_resolution(self):
        with tempfile.TemporaryDirectory() as lib_dir, tempfile.TemporaryDirectory() as app_dir:
            util_file = os.path.join(lib_dir, "utils.kl")
            with open(util_file, "w", encoding="utf-8") as f:
                f.write("int double_it(int x) { return x * 2; }\n")

            main_file = os.path.join(app_dir, "main.kl")
            with open(main_file, "w", encoding="utf-8") as f:
                f.write('import "utils.kl" as u;\nreturn u.double_it(21);\n')

            with open(main_file, "r", encoding="utf-8") as f:
                text = SourceText(f.read(), file_name=main_file)

            diag = DiagnosticBag()
            parser = Parser(text, diag)
            unit = parser.parse_compilation_unit()

            # Provide lib_dir in search_paths
            loader = ModuleLoader(diag, search_paths=[lib_dir])
            binder = Binder(diag, module_loader=loader, current_file=main_file)
            program = binder.bind_program(unit)
            self.assertFalse(diag.has_errors)

            emitter = LLVMEmitter()
            mod = emitter.emit_module(program)
            jit = LLVMJIT()
            ret = jit.run_ir(str(mod))
            self.assertEqual(ret, 42)


if __name__ == "__main__":
    unittest.main()
