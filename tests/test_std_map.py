import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT
from kale.codegen.c_emitter import CEmitter

class TestStdMap(unittest.TestCase):
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

    def test_int_map(self):
        code = """
        import "packages/std/collections/map.kl" as m;

        IntMap<int> my_map;
        my_map.init(16);

        my_map.put(10, 100);
        my_map.put(20, 200);
        my_map.put(30, 300);

        int sz = my_map.size();
        bool has_20 = my_map.contains(20);
        bool has_99 = my_map.contains(99);

        Option<int> val20 = my_map.get(20);
        int v20 = val20.unwrap();

        my_map.destroy();

        if (sz != 3) {
            return 1;
        }
        if (!has_20) {
            return 2;
        }
        if (has_99) {
            return 3;
        }
        if (v20 != 200) {
            return 4;
        }
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_string_map(self):
        code = """
        import "packages/std/collections/map.kl" as m;

        StringMap<int> token_map;
        token_map.init(16);

        token_map.put("keyword", 1);
        token_map.put("identifier", 2);
        token_map.put("literal", 3);

        int sz = token_map.size();
        bool has_id = token_map.contains("identifier");
        bool has_op = token_map.contains("operator");

        Option<int> val = token_map.get("literal");
        int lit_code = val.unwrap();

        token_map.destroy();

        if (sz != 3) {
            return 1;
        }
        if (!has_id) {
            return 2;
        }
        if (has_op) {
            return 3;
        }
        if (lit_code != 3) {
            return 4;
        }
        return 99;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 99)

if __name__ == "__main__":
    unittest.main()
