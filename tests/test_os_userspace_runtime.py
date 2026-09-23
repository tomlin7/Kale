import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSUserspaceRuntime(unittest.TestCase):
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

    def test_string_and_memory_primitives(self):
        code = r"""
        import "os/userspace/libkale.kl" as libc;

        // strlen
        if (libc.k_strlen("hello") != 5) return 1;
        if (libc.k_strlen("") != 0) return 2;

        // strcmp
        if (libc.k_strcmp("abc", "abc") != 0) return 3;
        if (libc.k_strcmp("abc", "abd") >= 0) return 4;

        // strcpy
        char[16] dest;
        libc.k_strcpy(&dest[0], "kale-os");
        if (dest[0] != (107 as char) || dest[4] != (45 as char)) return 5;

        // memset and memcmp
        uint8[8] b1;
        uint8[8] b2;
        libc.k_memset(&b1[0], 0xAA as uint8, 8);
        libc.k_memset(&b2[0], 0xAA as uint8, 8);
        if (libc.k_memcmp(&b1[0], &b2[0], 8) != 0) return 6;

        b2[7] = 0xBB as uint8;
        if (libc.k_memcmp(&b1[0], &b2[0], 8) == 0) return 7;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_user_heap_allocator_malloc_and_free(self):
        code = r"""
        import "os/userspace/libkale.kl" as libc;

        libc.UserHeap heap;
        libc.k_heap_init(&heap);

        if (heap.total_capacity != (4096 as uint32)) return 1;
        if (heap.allocated_bytes != (0 as uint32)) return 2;

        // Allocate 64 bytes
        int32 ptr1 = libc.k_malloc(&heap, 64 as uint32);
        if (ptr1 < 0) return 3;
        if (heap.allocated_bytes != (64 as uint32)) return 4;
        if (heap.block_count != (2 as uint32)) return 5;

        // Allocate 128 bytes
        int32 ptr2 = libc.k_malloc(&heap, 128 as uint32);
        if (ptr2 < 0 || ptr2 == ptr1) return 6;
        if (heap.allocated_bytes != (192 as uint32)) return 7;

        // Free first block
        bool ok = libc.k_free(&heap, ptr1);
        if (!ok) return 8;
        if (heap.allocated_bytes != (128 as uint32)) return 9;

        // Free second block and verify coalescing
        ok = libc.k_free(&heap, ptr2);
        if (!ok) return 10;
        if (heap.allocated_bytes != (0 as uint32)) return 11;
        if (heap.block_count != (1 as uint32)) return 12;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_posix_syscall_dispatcher(self):
        code = r"""
        import "os/userspace/libkale.kl" as libc;

        libc.SyscallFrame frame;
        
        // SYS_GETPID
        frame.nr = libc.SYS_GETPID;
        int64 ret = libc.k_dispatch_syscall(&frame);
        if (ret != (1001 as int64) || frame.err_no != 0) return 1;

        // SYS_WRITE to stdout (fd = 1)
        frame.nr = libc.SYS_WRITE;
        frame.arg1 = 1 as uint64; // stdout
        frame.arg3 = 12 as uint64; // 12 bytes
        ret = libc.k_dispatch_syscall(&frame);
        if (ret != (12 as int64) || frame.err_no != 0) return 2;

        // SYS_WRITE to invalid fd
        frame.arg1 = 99 as uint64;
        ret = libc.k_dispatch_syscall(&frame);
        if (ret != (-1 as int64) || frame.err_no != 9) return 3; // EBADF

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
