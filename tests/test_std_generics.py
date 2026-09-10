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

class TestStdGenerics(unittest.TestCase):
    def run_kale_jit(self, code: str):
        st = SourceText(code)
        diag = DiagnosticBag()
        loader = ModuleLoader([os.path.abspath("packages")], diag)
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

    def test_std_option(self):
        code = """
        import "packages/std/core/option.kl" as opt;

        Option<int> opt_val;
        opt_val.has_value = true;
        opt_val.value = 777;

        if (opt_val.is_some()) {
            print(opt_val.unwrap());
        }

        Option<int> opt_none;
        opt_none.has_value = false;
        int fallback = opt_none.unwrap_or(404);
        print(fallback);
        """
        ret = self.run_kale_jit(code)
        self.assertEqual(ret, 0)

    def test_std_result(self):
        code = """
        import "packages/std/core/option.kl" as opt;

        Result<int, string> res;
        res.is_ok = true;
        res.value = 200;

        if (res.ok()) {
            print(res.unwrap());
        }
        """
        ret = self.run_kale_jit(code)
        self.assertEqual(ret, 0)

    def test_std_generic_list(self):
        code = """
        import "packages/std/collections/generic_list.kl" as gl;

        List<int> numbers;
        numbers.init(4);
        numbers.push(10);
        numbers.push(20);
        numbers.push(30);

        print(numbers.size());
        print(numbers.get(1));
        print(numbers[2]);

        numbers.destroy();
        """
        ret = self.run_kale_jit(code)
        self.assertEqual(ret, 0)
