import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSKernelPanic(unittest.TestCase):
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

    def test_panic_context_init(self):
        code = r"""
        import "os/kernel/panic.kl" as p;

        p.PanicContext ctx;
        uint8[16] msg;
        msg[0] = 79 as uint8; // 'O'
        msg[1] = 79 as uint8; // 'O'
        msg[2] = 80 as uint8; // 'P'
        msg[3] = 83 as uint8; // 'S'
        msg[4] = 0 as uint8;

        p.panic_init_context(&ctx, p.FAULT_PAGE_FAULT, 2 as uint64, &msg[0]);

        if (!ctx.is_valid) return 1;
        if (ctx.regs.vector != p.FAULT_PAGE_FAULT) return 2;
        if (ctx.regs.err_code != (2 as uint64)) return 3;
        if (ctx.message[0] != (79 as uint8) || ctx.message[3] != (83 as uint8)) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_panic_stack_unwinding(self):
        code = r"""
        import "os/kernel/panic.kl" as p;

        p.PanicContext ctx;
        p.panic_init_context(&ctx, p.FAULT_GPF, 0 as uint64, null);

        // Simulate 3 stack frames in a 32-element uint64 array
        // uint64 indices:
        // Frame 0: index 0 (rbp=1000): next_rbp=1032, ret_rip=0x00401000
        // Frame 1: index 4 (rbp=1032): next_rbp=1064, ret_rip=0x00402000
        // Frame 2: index 8 (rbp=1064): next_rbp=1200 (out of bounds), ret_rip=0x00403000
        uint64[32] stack_buf;
        int i = 0;
        while (i < 32) {
            stack_buf[i] = 0 as uint64;
            i = i + 1;
        }

        uint64 base = 1000 as uint64;
        // Frame 0
        stack_buf[0] = base + (32 as uint64); // next rbp = 1032
        stack_buf[1] = 0x00401000 as uint64;  // ret rip

        // Frame 1
        stack_buf[4] = base + (64 as uint64); // next rbp = 1064
        stack_buf[5] = 0x00402000 as uint64;  // ret rip

        // Frame 2
        stack_buf[8] = base + (200 as uint64);// next rbp (out of bounds)
        stack_buf[9] = 0x00403000 as uint64;  // ret rip

        p.panic_unwind_stack(&ctx, &stack_buf[0], base, base, base + (80 as uint64));

        if (ctx.backtrace_count != 3) return 1;
        if (ctx.backtrace[0] != (0x00401000 as uint64)) return 2;
        if (ctx.backtrace[1] != (0x00402000 as uint64)) return 3;
        if (ctx.backtrace[2] != (0x00403000 as uint64)) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_panic_stack_bounds_protection(self):
        code = r"""
        import "os/kernel/panic.kl" as p;

        p.PanicContext ctx;
        p.panic_init_context(&ctx, p.FAULT_DOUBLE_FAULT, 0 as uint64, null);

        uint64[16] stack_buf;
        // Invalid RBP far outside bottom/top range
        p.panic_unwind_stack(&ctx, &stack_buf[0], 0xDEADBEEF as uint64, 1000 as uint64, 2000 as uint64);

        if (ctx.backtrace_count != 0) return 1;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_panic_core_dump_serialization(self):
        code = r"""
        import "os/kernel/panic.kl" as p;

        p.PanicContext ctx;
        uint8[16] msg;
        msg[0] = 67 as uint8; // 'C'
        msg[1] = 82 as uint8; // 'R'
        msg[2] = 65 as uint8; // 'A'
        msg[3] = 83 as uint8; // 'S'
        msg[4] = 72 as uint8; // 'H'
        msg[5] = 0 as uint8;

        p.panic_init_context(&ctx, p.FAULT_PAGE_FAULT, 0 as uint64, &msg[0]);
        ctx.regs.rip = 0x00007FFFF7B00124 as uint64;
        ctx.regs.rsp = 0x00007FFFFFFFE000 as uint64;
        ctx.regs.cr2 = 0x00000000DEAD0000 as uint64;
        ctx.backtrace_count = 2;

        p.CoreDumpHeader hdr;
        p.panic_serialize_core_dump(&ctx, &hdr);

        if (hdr.magic != p.PANIC_MAGIC) return 1;
        if (hdr.vector != p.FAULT_PAGE_FAULT) return 2;
        if (hdr.rip != (0x00007FFFF7B00124 as uint64)) return 3;
        if (hdr.rsp != (0x00007FFFFFFFE000 as uint64)) return 4;
        if (hdr.cr2 != (0x00000000DEAD0000 as uint64)) return 5;
        if (hdr.backtrace_count != (2 as uint32)) return 6;
        if (hdr.message[0] != (67 as uint8)) return 7;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
