import unittest
import tempfile
import os
import shutil
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.codegen.c_emitter import CEmitter
from kale.codegen.compiler_driver import CompilerDriver

class TestCodegen(unittest.TestCase):
    def test_c_emitter_generates_valid_c_structure(self):
        text = SourceText("""
        int a = 10;
        int b = 20;
        int c = a + b;
        print("Sum:", c);
        """)
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)

        emitter = CEmitter()
        c_code = emitter.emit(program)
        self.assertIn("#include <stdio.h>", c_code)
        self.assertIn("int main(int argc, char** argv) {", c_code)
        self.assertIn("long long a = 10;", c_code)
        self.assertIn("long long b = 20;", c_code)
        self.assertIn("long long c = (a + b);", c_code)
        self.assertIn('_kale_print_str("Sum:");', c_code)
        self.assertIn("_kale_print_int(c);", c_code)

    def test_native_compile_and_run(self):
        driver = CompilerDriver()
        if not driver.compiler:
            self.skipTest("No C compiler found on system")

        text = SourceText("""
        int x = 5;
        int y = 7;
        int z = x * y;
        print("Product:", z);
        """)
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)

        emitter = CEmitter()
        c_code = emitter.emit(program)

        with tempfile.TemporaryDirectory() as tmp_dir:
            c_file = os.path.join(tmp_dir, "test_out.c")
            with open(c_file, "w") as f:
                f.write(c_code)

            exe_file = driver.compile(c_file)
            self.assertTrue(os.path.exists(exe_file))

            res = driver.run(exe_file)
            self.assertEqual(res.returncode, 0)
            self.assertIn("Product: 35", res.stdout)

    def test_while_loop_execution(self):
        driver = CompilerDriver()
        if not driver.compiler:
            self.skipTest("No C compiler found on system")

        text = SourceText("""
        int count = 0;
        int sum = 0;
        while (count < 5) {
            sum += count;
            count++;
        }
        print("Total:", sum);
        """)
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)

        emitter = CEmitter()
        c_code = emitter.emit(program)

        with tempfile.TemporaryDirectory() as tmp_dir:
            c_file = os.path.join(tmp_dir, "test_loop.c")
            with open(c_file, "w") as f:
                f.write(c_code)

            exe_file = driver.compile(c_file)
            res = driver.run(exe_file)
            self.assertEqual(res.returncode, 0)
            self.assertIn("Total: 10", res.stdout)

if __name__ == "__main__":
    unittest.main()
