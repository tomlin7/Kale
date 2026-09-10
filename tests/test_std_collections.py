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

class TestStandardCollections(unittest.TestCase):
    def test_int_list_jit(self):
        text = SourceText('''
        import "packages/std/collections/list.kl" as col;

        col.IntList list = col.create_list(4);
        list.push(10);
        list.push(20);
        list.push(30);
        list.push(40);
        list.push(50); // triggers dynamic growth

        print(list.size());
        print(list[0], list[2], list[4]);

        int popped = list.pop();
        print(popped, list.size());

        list.destroy();
        ''')
        diag = DiagnosticBag()
        loader = ModuleLoader(diag)
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, f"Parse errors: {[d.message for d in diag]}")

        binder = Binder(diag, module_loader=loader)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, f"Bind errors: {[d.message for d in diag]}")

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)

        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 0)

    def test_byte_buffer_jit(self):
        text = SourceText('''
        import "packages/std/collections/buffer.kl" as buf_mod;

        buf_mod.ByteBuffer buf = buf_mod.create_buffer(4);
        buf.append_str("Hello");
        buf.append_char(' ');
        buf.append_str("World!");

        print(buf.size());
        print(buf.to_string());
        print(buf[0], buf[6]);

        buf.destroy();
        ''')
        diag = DiagnosticBag()
        loader = ModuleLoader(diag)
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, f"Parse errors: {[d.message for d in diag]}")

        binder = Binder(diag, module_loader=loader)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, f"Bind errors: {[d.message for d in diag]}")

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)

        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 0)

    def test_string_module_jit(self):
        text = SourceText('''
        import "packages/std/core/string.kl" as str_util;

        int len = str_util.length("Kale Monorepo");
        bool eq = str_util.equals("abc", "abc");
        bool neq = str_util.equals("abc", "xyz");
        print(len, eq, neq);
        ''')
        diag = DiagnosticBag()
        loader = ModuleLoader(diag)
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, f"Parse errors: {[d.message for d in diag]}")

        binder = Binder(diag, module_loader=loader)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, f"Bind errors: {[d.message for d in diag]}")

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)

        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 0)

    def test_collections_c_emitter(self):
        text = SourceText('''
        import "packages/std/collections/list.kl" as col;

        col.IntList list = col.create_list(4);
        list.push(123);
        int v = list[0];
        list.destroy();
        ''')
        diag = DiagnosticBag()
        loader = ModuleLoader(diag)
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors)

        binder = Binder(diag, module_loader=loader)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)

        c_emitter = CEmitter()
        c_code = c_emitter.emit(program)
        self.assertIn("struct IntList", c_code)
        self.assertIn("kale_list_create_list", c_code)
        self.assertIn("kale_IntList_push", c_code)

if __name__ == "__main__":
    unittest.main()
