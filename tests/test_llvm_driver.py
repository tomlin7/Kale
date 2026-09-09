import unittest
import os
import tempfile
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_driver import LLVMDriver

class TestLLVMDriver(unittest.TestCase):
    def test_compile_ll_to_executable_and_run(self):
        driver = LLVMDriver()
        if not driver.clang_path:
            self.skipTest("Clang not found")

        text = SourceText("""
        int x = 100;
        int y = 25;
        print("Division:", x / y);
        """)
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)

        with tempfile.TemporaryDirectory() as tmp_dir:
            ll_path = os.path.join(tmp_dir, "test.ll")
            with open(ll_path, "w", encoding="utf-8") as f:
                f.write(str(mod))

            exe_path = driver.compile_ll(ll_path)
            self.assertTrue(os.path.exists(exe_path))

            res = driver.run(exe_path)
            self.assertEqual(res.returncode, 0)
            self.assertIn("Division: 4", res.stdout)

if __name__ == "__main__":
    unittest.main()
